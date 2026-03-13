"""
access/services/access_service.py
==================================
All user-scoped data-access logic for the RBAC system.

Public surface
--------------
get_child_org_units(org_unit)
    Returns a QuerySet of ALL recursive descendant OrgUnits for a single
    unit. Uses a PostgreSQL recursive CTE — one DB round-trip.

get_user_accessible_unit_ids(user) -> list[str]
    Returns every OrgUnit UUID the user can see (direct assignments +
    all descendants). Multi-root CTE — one DB round-trip. Result cached
    on the user object for the lifetime of the request.

get_user_accessible_roads(user) -> QuerySet[Road]
    Full pipeline: user → CTE unit IDs → projects → roads.
    2 DB queries total. Admins bypass the filter entirely.

is_admin(user) -> bool
user_has_access_to_unit(user, org_unit_id) -> bool
assign_user_to_unit(assigning_user, target_user, org_unit_id, role)
remove_user_from_unit(assigning_user, target_user, org_unit_id)
"""
from __future__ import annotations

from django.db.models import QuerySet

from access.models import UserOrgAccess
from orgs.models import OrgUnit


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_descendants_from_db(org_unit_id) -> list:
    """
    Fetches all descendant OrgUnit IDs for a SINGLE root unit.

    Returns a flat list of UUID strings (includes the root unit itself).
    Kept for use by hierarchy_service and other single-unit lookups.
    """
    from django.db import connection  # noqa: PLC0415

    sql = """
        WITH RECURSIVE subtree AS (
            SELECT id
            FROM   orgs_orgunit
            WHERE  id = %s

            UNION ALL

            SELECT child.id
            FROM   orgs_orgunit child
            INNER JOIN subtree parent ON child.parent_unit_id = parent.id
        )
        SELECT id FROM subtree;
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [str(org_unit_id)])
        rows = cursor.fetchall()
    return [str(row[0]) for row in rows]


def _get_all_descendant_ids_for_user(user) -> list[str]:
    """
    Resolves every accessible OrgUnit ID for a user in a SINGLE database
    round-trip using a multi-root recursive CTE.

    Key optimisation over the old per-unit loop
    -------------------------------------------
    Old approach (N+1 at service level)::

        for unit in direct_units:           # Python loop
            ids += CTE(unit.id)             # 1 query per unit

    New approach (1 query total)::

        CTE anchor = all direct units simultaneously
        CTE recursive step = all children of already-found units
        → one query regardless of how many direct units the user has

    SQL plan
    --------
    1. Anchor   — JOIN UserOrgAccess on user_id + is_active to seed the CTE
                  with all root units in one shot.
    2. Recursive — standard adjacency-list expansion.
    3. DISTINCT  — deduplicate (a unit can appear via multiple access grants).
    """
    from django.db import connection  # noqa: PLC0415

    sql = """
        WITH RECURSIVE subtree AS (

            -- Anchor: every OrgUnit the user is directly assigned to
            SELECT ou.id
            FROM   orgs_orgunit ou
            INNER  JOIN access_userorgaccess uoa
                     ON uoa.org_unit_id = ou.id
            WHERE  uoa.user_id  = %s
              AND  uoa.is_active = TRUE

            UNION ALL

            -- Recursive step: pull in every child of an already-found unit
            SELECT child.id
            FROM   orgs_orgunit child
            INNER  JOIN subtree ON child.parent_unit_id = subtree.id
        )
        SELECT DISTINCT id FROM subtree;
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [str(user.pk)])
        rows = cursor.fetchall()
    return [str(row[0]) for row in rows]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_user_org_units(user) -> QuerySet:
    """
    Returns the DIRECT OrgUnits assigned to a user via active UserOrgAccess records.
    """
    return OrgUnit.objects.filter(
        user_accesses__user=user,
        user_accesses__is_active=True,
    ).distinct()


# ---------------------------------------------------------------------------
# Hierarchy helpers
# ---------------------------------------------------------------------------

def get_child_org_units(org_unit) -> QuerySet:
    """
    Returns a QuerySet of ALL recursive descendant OrgUnits for the given
    unit, **excluding the unit itself**.

    Uses a single PostgreSQL recursive CTE (one DB round-trip) via
    orgs.services.hierarchy_service.get_descendant_ids().

    Example
    -------
    For the tree  HO → [RO-North, RO-South] → [PIU-A, PIU-B, PIU-C]:

        get_child_org_units(HO)      # → [RO-North, RO-South, PIU-A, PIU-B, PIU-C]
        get_child_org_units(RO-North) # → [PIU-A, PIU-B]

    Args:
        org_unit: An OrgUnit instance (must have .pk set).

    Returns:
        Lazy QuerySet of OrgUnit instances with
        select_related('level', 'organization', 'parent_unit').
    """
    from orgs.services.hierarchy_service import get_descendant_ids  # noqa: PLC0415

    ids = get_descendant_ids(str(org_unit.pk), include_self=False)
    return (
        OrgUnit.objects
        .filter(id__in=ids)
        .select_related("level", "organization", "parent_unit")
    )


def get_user_accessible_unit_ids(user) -> list:
    """
    THE core access resolution function.

    Algorithm:
    1. Fetch direct OrgUnits the user is assigned to.
    2. For each direct unit, run the recursive CTE to fetch ALL descendants.
    3. Return a de-duplicated flat list of accessible unit IDs.

    Result is cached on the user object per request (simple in-memory cache).
    In production, replace with Redis caching:
        cache_key = f"accessible_units:{user.id}"
        cached = cache.get(cache_key)
        if cached: return cached
        ... compute ...
        cache.set(cache_key, result, timeout=60)
    """
    cache_attr = "_accessible_unit_ids_cache"
    if hasattr(user, cache_attr):
        return getattr(user, cache_attr)

    # Single-query multi-root CTE — O(1) DB calls regardless of direct-unit count
    result = _get_all_descendant_ids_for_user(user)
    setattr(user, cache_attr, result)
    return result


def get_user_accessible_roads(user) -> QuerySet:
    """
    Returns a QuerySet of every Road the user is permitted to see.

    Access pipeline
    ---------------
    Step 1 — Resolve accessible OrgUnit IDs (multi-root recursive CTE):

        WITH RECURSIVE subtree AS (
            -- anchor: OrgUnits the user is directly assigned to
            SELECT ou.id FROM orgs_orgunit ou
            JOIN   access_userorgaccess uoa ON uoa.org_unit_id = ou.id
            WHERE  uoa.user_id = <user_pk> AND uoa.is_active = TRUE

            UNION ALL
            -- expand children
            SELECT child.id FROM orgs_orgunit child
            JOIN   subtree ON child.parent_unit_id = subtree.id
        )
        SELECT DISTINCT id FROM subtree;

    Step 2 — Filter Roads through the OrgUnit set (single ORM query):

        Road
          .filter(project__org_unit_id__in=<unit_ids from Step 1>)
          .select_related(project, project__org_unit, project__organization, ...)

    Total: 2 DB queries regardless of tree depth or user assignment count.
    Admins bypass both steps and receive an unrestricted queryset (1 query).

    Result is lazy — callers can chain .filter(), .order_by(), .values(), etc.

    Args:
        user: Any Django user instance (authenticated).

    Returns:
        Lazy QuerySet[Road] with pre-joined project and org fields.
    """
    from roads.models import Road  # noqa: PLC0415 (lazy import avoids circular dep)

    base_qs = Road.objects.select_related(
        "project",                       # Road → Project
        "project__org_unit",             # Project → OrgUnit (for ownership display)
        "project__org_unit__level",      # OrgUnit → HierarchyLevel
        "project__organization",         # Project → Organization
    )

    # Admins see every road — no filtering needed
    if is_admin(user):
        return base_qs.all()

    # Regular users: scope to their accessible OrgUnit subtree
    accessible_unit_ids = get_user_accessible_unit_ids(user)

    if not accessible_unit_ids:
        return base_qs.none()

    return base_qs.filter(project__org_unit_id__in=accessible_unit_ids)


def get_user_role_in_unit(user, org_unit_id) -> str | None:
    """
    Returns the user's DIRECT role for a specific org unit.
    Returns None if no direct assignment exists.
    Does NOT check inherited access.
    """
    try:
        access = UserOrgAccess.objects.get(
            user=user,
            org_unit_id=org_unit_id,
            is_active=True,
        )
        return access.role
    except UserOrgAccess.DoesNotExist:
        return None


def is_admin(user) -> bool:
    """Returns True if user is a Django superuser or has any admin-role access."""
    if getattr(user, "is_superuser", False):
        return True
    return UserOrgAccess.objects.filter(
        user=user,
        role=UserOrgAccess.RoleChoices.ADMIN,
        is_active=True,
    ).exists()


def user_has_access_to_unit(user, org_unit_id) -> bool:
    """
    Returns True if org_unit_id is in the user's accessible unit set.
    Used by HasOrgUnitAccess permission class.
    """
    if is_admin(user):
        return True
    accessible = get_user_accessible_unit_ids(user)
    return str(org_unit_id) in {str(uid) for uid in accessible}


def assign_user_to_unit(assigning_user, target_user, org_unit_id, role) -> UserOrgAccess:
    """
    Creates or updates a UserOrgAccess record.
    Uses update_or_create so duplicate calls are idempotent.

    Raises:
        PermissionError if assigning_user is not admin.
        ValueError if role is not a valid RoleChoices value.
    """
    if not is_admin(assigning_user):
        raise PermissionError("Only admins can assign user access.")

    valid_roles = [r[0] for r in UserOrgAccess.RoleChoices.choices]
    if role not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. Valid: {valid_roles}")

    access, _ = UserOrgAccess.objects.update_or_create(
        user=target_user,
        org_unit_id=org_unit_id,
        defaults={
            "role":        role,
            "assigned_by": assigning_user,
            "is_active":   True,
        },
    )
    # Bust the cache for the target user
    if hasattr(target_user, "_accessible_unit_ids_cache"):
        del target_user._accessible_unit_ids_cache

    return access


def remove_user_from_unit(assigning_user, target_user, org_unit_id) -> None:
    """
    Soft-deletes a UserOrgAccess record (sets is_active=False).

    Raises:
        PermissionError if assigning_user is not admin.
    """
    if not is_admin(assigning_user):
        raise PermissionError("Only admins can remove user access.")

    UserOrgAccess.objects.filter(
        user=target_user,
        org_unit_id=org_unit_id,
    ).update(is_active=False)

    if hasattr(target_user, "_accessible_unit_ids_cache"):
        del target_user._accessible_unit_ids_cache

