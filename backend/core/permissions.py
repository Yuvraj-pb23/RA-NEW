from rest_framework import permissions
from accounts.models import SystemRole

class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to super admins.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == SystemRole.SUPER_ADMIN)

class IsOrgAdmin(permissions.BasePermission):
    """
    Allows access to org admins. Super admins also implicitly get access.
    """
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False
        return request.user.role in [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]

class IsLevelUser(permissions.BasePermission):
    """
    General access for logged in hierarchical level users.
    """
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False
        return request.user.role in [
            SystemRole.SUPER_ADMIN, 
            SystemRole.ORG_ADMIN, 
            SystemRole.HO_USER, 
            SystemRole.RO_USER, 
            SystemRole.PIU_USER, 
            SystemRole.PROJECT_USER
        ]

class IsOrgAdminOrReadOnly(permissions.BasePermission):
    """
    Allows write access to org admins. Super admins also implicitly get access.
    Allows read to any authenticated user.
    """
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role in [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]
