from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import UserOrgAccess


def _get_user_role_map(user):
    """
    Returns {org_unit_id: role} for the user.
    Cached on the request object to avoid multiple DB hits per request.
    """
    if not hasattr(user, "_role_map_cache"):
        user._role_map_cache = UserOrgAccess.get_user_roles(user)
    return user._role_map_cache


def is_admin(user) -> bool:
    """Returns True if user has any admin-role assignment."""
    if user.is_superuser:
        return True
    return user.role in ['SUPER_ADMIN', 'ORG_ADMIN', 'HO_USER']


# =============================================================================
# Permission Classes
# =============================================================================

class IsAdminRole(BasePermission):
    """
    Allows access only to users with role=ADMIN in any org,
    or Django superusers.

    Usage:
        permission_classes = [IsAuthenticated, IsAdminRole]
    """

    message = "Admin role required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and is_admin(request.user)
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Full access for Admin role.
    Read-only (GET, HEAD, OPTIONS) for all authenticated users.

    Usage:
        permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    """

    message = "Admin role required for write operations."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return is_admin(request.user)


class HasOrgUnitAccess(BasePermission):
    """
    Object-level permission.

    Checks whether the requesting user has the target object's org_unit
    in their accessible unit IDs (direct assignment OR ancestor inheritance).

    Requires the view to call check_object_permissions(request, obj).

    Resolves the org_unit_id from the object in this order:
      1. obj.org_unit_id       (Project, OrgUnit via UserOrgAccess)
      2. obj.project.org_unit_id  (Road)
      3. obj.org_unit.id       (fallback via relation)

    Admins always pass.
    """

    message = "You do not have access to this organizational unit."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if is_admin(user):
            return True

        # Import lazily to avoid circular imports at module level
        from access.services.access_service import get_user_accessible_unit_ids  # noqa: PLC0415

        accessible_ids = set(get_user_accessible_unit_ids(user))

        # Resolve org_unit_id from different model shapes
        org_unit_id = getattr(obj, "org_unit_id", None)
        if org_unit_id is None:
            # Road → project → org_unit_id
            project = getattr(obj, "project", None)
            if project is not None:
                org_unit_id = getattr(project, "org_unit_id", None)

        return str(org_unit_id) in {str(uid) for uid in accessible_ids}


class IsSelfOrAdmin(BasePermission):
    """
    Object-level permission for User endpoints.
    A user can only read/edit their own profile unless they are Admin.
    """

    message = "You can only access your own profile."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if is_admin(request.user):
            return True
        # obj is a User instance
        return obj.pk == request.user.pk
