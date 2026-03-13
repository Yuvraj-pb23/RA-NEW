"""
hierarchy_service.py — orgs app
================================
All recursive OrgUnit hierarchy traversal lives here.
Views / serializers must never bypass this service for tree queries.
"""
from __future__ import annotations

from django.db import connection

from orgs.models import HierarchyLevel, OrgUnit


# ---------------------------------------------------------------------------
# Low-level CTE helpers
# ---------------------------------------------------------------------------

_DESCENDANTS_SQL = """
WITH RECURSIVE subtree AS (
    SELECT id, name, parent_unit_id, level_id, organization_id, 0 AS depth
    FROM   orgs_orgunit
    WHERE  id = %s

    UNION ALL

    SELECT child.id, child.name, child.parent_unit_id,
           child.level_id, child.organization_id, subtree.depth + 1
    FROM   orgs_orgunit child
    INNER  JOIN subtree ON child.parent_unit_id = subtree.id
)
SELECT id, depth FROM subtree
{exclude_self}
ORDER BY depth;
"""

_ANCESTORS_SQL = """
WITH RECURSIVE ancestors AS (
    SELECT id, name, parent_unit_id, level_id, organization_id, 0 AS depth
    FROM   orgs_orgunit
    WHERE  id = %s

    UNION ALL

    SELECT parent.id, parent.name, parent.parent_unit_id,
           parent.level_id, parent.organization_id, ancestors.depth - 1
    FROM   orgs_orgunit parent
    INNER  JOIN ancestors ON ancestors.parent_unit_id = parent.id
)
SELECT id, depth FROM ancestors
WHERE  id != %s
ORDER BY depth;
"""


def _fetch_ids_and_depths(sql: str, *params) -> list[tuple]:
    """Runs a raw CTE query and returns (id, depth) rows."""
    with connection.cursor() as cursor:
        cursor.execute(sql, list(params))
        return cursor.fetchall()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_descendants(org_unit_id, include_self: bool = True) -> list[OrgUnit]:
    """
    Returns all OrgUnit objects in the subtree rooted at *org_unit_id*,
    ordered shallow → deep.

    Uses a single PostgreSQL recursive CTE (one DB round-trip).

    Args:
        org_unit_id: UUID or str PK of the root unit.
        include_self: If False, the root unit itself is excluded.

    Returns:
        List of OrgUnit instances with select_related('level', 'organization').
    """
    exclude_clause = "WHERE depth > 0" if not include_self else ""
    sql = _DESCENDANTS_SQL.format(exclude_self=exclude_clause)
    rows = _fetch_ids_and_depths(sql, str(org_unit_id))
    ordered_ids = [str(row[0]) for row in rows]

    units_by_id = {
        str(u.id): u
        for u in OrgUnit.objects.filter(id__in=ordered_ids).select_related(
            "level", "organization", "parent_unit"
        )
    }
    # Preserve CTE ordering
    return [units_by_id[uid] for uid in ordered_ids if uid in units_by_id]


def get_descendant_ids(org_unit_id, include_self: bool = True) -> list[str]:
    """
    Lightweight variant — returns only UUIDs (as strings), no ORM objects.
    Preferred for permission checks and filtered querysets.
    """
    exclude_clause = "WHERE depth > 0" if not include_self else ""
    sql = _DESCENDANTS_SQL.format(exclude_self=exclude_clause)
    rows = _fetch_ids_and_depths(sql, str(org_unit_id))
    return [str(row[0]) for row in rows]


def get_ancestors(org_unit_id) -> list[OrgUnit]:
    """
    Returns the ancestor chain from the immediate parent up to the root,
    ordered root-first (depth ascending after inversion).

    Used for breadcrumb navigation.

    Args:
        org_unit_id: UUID or str PK of the target unit.

    Returns:
        List of OrgUnit instances; empty list if unit is already a root.
    """
    rows = _fetch_ids_and_depths(_ANCESTORS_SQL, str(org_unit_id), str(org_unit_id))
    if not rows:
        return []

    # CTE returns ascending depth (0 = self which we excluded).
    # Sort by depth so closest parent comes first, then reverse for root-first.
    ordered_ids = [str(row[0]) for row in sorted(rows, key=lambda r: r[1], reverse=True)]

    units_by_id = {
        str(u.id): u
        for u in OrgUnit.objects.filter(id__in=ordered_ids).select_related(
            "level", "organization"
        )
    }
    return [units_by_id[uid] for uid in ordered_ids if uid in units_by_id]


def build_tree(org_id) -> list[dict]:
    """
    Builds a fully nested tree structure for an entire organization.

    Single DB query — fetches all OrgUnits for the org and assembles
    the tree in Python using a dict lookup (O(n)).

    Returns:
        List of root-level node dicts with the shape::

            {
                "id":       "uuid",
                "name":     "HO Delhi",
                "level":    "HO",
                "depth":    0,
                "children": [ {...}, ... ]
            }
    """
    units = OrgUnit.objects.filter(organization_id=org_id).select_related(
        "level", "parent_unit"
    ).order_by("level__level_order", "name")

    node_map: dict[str, dict] = {}
    for unit in units:
        node_map[str(unit.id)] = {
            "id":            str(unit.id),
            "name":          unit.name,
            "level":         unit.level.level_name if unit.level else None,
            "level_order":   unit.level.level_order if unit.level else None,
            "parent_unit_id": str(unit.parent_unit_id) if unit.parent_unit_id else None,
            "children":      [],
        }

    roots: list[dict] = []
    for node in node_map.values():
        parent_id = node["parent_unit_id"]
        if parent_id and parent_id in node_map:
            node_map[parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


def validate_parent_level(child_level_id, parent_unit_id) -> bool:
    """
    Checks that the parent unit's HierarchyLevel is exactly one step above
    the child's level (level_order difference == 1).

    Returns True if valid, False otherwise.

    Example::
        HO (order=1) → RO (order=2) → PIU (order=3)
        validate_parent_level(PIU.id, some_RO_unit.id) → True
        validate_parent_level(PIU.id, some_HO_unit.id) → False
    """
    try:
        child_level = HierarchyLevel.objects.get(id=child_level_id)
        parent_unit = OrgUnit.objects.select_related("level").get(id=parent_unit_id)
    except (HierarchyLevel.DoesNotExist, OrgUnit.DoesNotExist):
        return False

    if parent_unit.level is None:
        return False

    return (child_level.level_order - parent_unit.level.level_order) == 1


def get_depth(org_unit_id) -> int:
    """
    Returns the depth of the unit in its tree (root = 0).
    Walks the ancestor chain iteratively (max depth ≈ number of HierarchyLevels).
    """
    depth = 0
    current_id = str(org_unit_id)

    while True:
        try:
            unit = OrgUnit.objects.only("parent_unit_id").get(id=current_id)
        except OrgUnit.DoesNotExist:
            break
        if unit.parent_unit_id is None:
            break
        current_id = str(unit.parent_unit_id)
        depth += 1

    return depth
#     """Returns the depth of an org unit in the tree (root = 0)."""
#     pass
# =============================================================================
