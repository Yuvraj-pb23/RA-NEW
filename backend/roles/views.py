"""
roles/views.py
==============
API views for Role and RolePermission management.

Supervisor roles: grant org-wide visibility but cannot write roles.
Hierarchy roles: visibility scoped to lower hierarchy_level values.
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from .models import Role, RolePermission
from .serializers import (
    RoleSerializer,
    RoleCreateUpdateSerializer,
    RoleMinimalSerializer,
)


class IsOrgAdminPermission(BasePermission):
    """Write operations (create/update/delete) require ORG_ADMIN or SUPER_ADMIN."""
    message = "Only Org Admins can create, edit, or delete roles."

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        role = getattr(request.user, "role", None)
        return role in ("ORG_ADMIN", "SUPER_ADMIN")


def _user_has_supervisor_visibility(user) -> bool:
    """
    Return True if the user's custom_role is a Supervisor role (or has supervisor visibility).
    Always False for ORG_ADMIN/SUPER_ADMIN (they have their own gate-keeping).
    """
    custom_role = getattr(user, "custom_role", None)
    if custom_role is None:
        return False
    return custom_role.is_supervisor_role or custom_role.has_supervisor_visibility


class RoleViewSet(viewsets.ModelViewSet):
    """
    CRUD for dynamic Org Roles.

    list     GET    /api/v1/roles/
    create   POST   /api/v1/roles/          (ORG_ADMIN only)
    retrieve GET    /api/v1/roles/<id>/
    update   PUT    /api/v1/roles/<id>/     (ORG_ADMIN only)
    partial  PATCH  /api/v1/roles/<id>/     (ORG_ADMIN only)
    destroy  DELETE /api/v1/roles/<id>/     (ORG_ADMIN only)

    Query params:
      ?status=active          filter by status
      ?organization=<id>      filter by org (SUPER_ADMIN only)
      ?minimal=1              use lightweight serializer for dropdowns
    """

    permission_classes = [IsAuthenticated, IsOrgAdminPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "hierarchy_level", "is_supervisor_role"]
    search_fields = ["role_name"]
    ordering_fields = ["hierarchy_level", "role_name", "created_at", "is_supervisor_role"]
    ordering = ["is_supervisor_role", "hierarchy_level", "role_name"]

    def get_queryset(self):
        user = self.request.user
        qs = Role.objects.select_related(
            "organization", "parent_role", "created_by"
        ).prefetch_related("permissions")

        # Super Admin can see all orgs
        if getattr(user, "role", None) == "SUPER_ADMIN":
            org_id = self.request.query_params.get("organization")
            if org_id:
                return qs.filter(organization_id=org_id)
            return qs

        # All other users: scope to their own org
        if not user.organization:
            return qs.none()

        qs = qs.filter(organization=user.organization)

        # Org Admin sees all roles in their org
        if getattr(user, "role", None) == "ORG_ADMIN":
            return qs

        # Supervisor role users see ALL roles in their org (excluding ORG_ADMIN system roles)
        if _user_has_supervisor_visibility(user):
            return qs

        # Hierarchy users: only see roles with a HIGHER hierarchy level number (lower authority)
        custom_role = getattr(user, "custom_role", None)
        if custom_role and not custom_role.is_supervisor_role and custom_role.hierarchy_level is not None:
            # Can see own role level and below (higher level number)
            qs = qs.filter(
                is_supervisor_role=False,
                hierarchy_level__gte=custom_role.hierarchy_level,
            )
        else:
            # No custom role assigned — show nothing extra
            qs = qs.none()

        return qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RoleCreateUpdateSerializer
        if self.request.query_params.get("minimal"):
            return RoleMinimalSerializer
        return RoleSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user_count = instance.users.count()
        if user_count:
            return Response(
                {
                    "error": True,
                    "message": (
                        f"Cannot delete role '{instance.role_name}' — "
                        f"{user_count} user(s) are assigned to it. "
                        "Reassign users first."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)
