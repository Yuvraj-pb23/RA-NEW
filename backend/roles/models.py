"""
roles/models.py
===============
Dynamic role management models.

Two types of roles:
  1. Hierarchy roles  — have hierarchy_level and parent_role, normal cascading access
  2. Supervisor roles — is_supervisor_role=True, no level/parent, flat org-wide visibility
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    """
    A custom, organization-specific role created by an Org Admin.

    ── Hierarchy Role (is_supervisor_role=False) ──
      hierarchy_level: lower number = higher authority (e.g. 1 = top-most)
      parent_role:     the role directly above this one in the hierarchy

    ── Supervisor Role (is_supervisor_role=True) ──
      Does NOT belong to the hierarchy.
      hierarchy_level and parent_role are NOT required / not meaningful.
      Grants org-wide read visibility ONLY — cannot create/delete roles or
      modify Org Admin permissions.
    """

    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "orgs.Organization",
        on_delete=models.CASCADE,
        related_name="custom_roles",
        db_index=True,
    )
    role_name = models.CharField(_("role name"), max_length=100)

    # ── Hierarchy Role fields (not used for Supervisor roles) ─────────────
    hierarchy_level = models.PositiveSmallIntegerField(
        _("hierarchy level"),
        null=True,
        blank=True,
        help_text=_(
            "Lower number = higher authority. e.g. 1 is the top-most role. "
            "Leave blank for Supervisor roles."
        ),
    )
    parent_role = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_roles",
        db_index=True,
        help_text=_("The role that directly supervises this role. Leave blank for Supervisor roles."),
    )

    # ── Supervisor Role flag ───────────────────────────────────────────────
    is_supervisor_role = models.BooleanField(
        _("supervisor role"),
        default=False,
        db_index=True,
        help_text=_(
            "If True, this is a special non-hierarchical Supervisor role. "
            "Users with this role gain org-wide visibility (view all roles, users, "
            "dashboards) but cannot create/delete roles or modify Org Admin permissions. "
            "hierarchy_level and parent_role are ignored for Supervisor roles."
        ),
    )

    # ── Legacy flag (kept for backwards-compat, superseded by is_supervisor_role) ─
    has_supervisor_visibility = models.BooleanField(
        _("supervisor visibility access"),
        default=False,
        help_text=_(
            "Deprecated — use is_supervisor_role instead. "
            "If enabled, users can view all roles and users org-wide."
        ),
    )

    status = models.CharField(
        _("status"),
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_roles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roles_role"
        verbose_name = _("role")
        verbose_name_plural = _("roles")
        ordering = ["organization", "is_supervisor_role", "hierarchy_level", "role_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "role_name"],
                name="uq_role_org_name",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "status"], name="idx_role_org_status"),
            models.Index(fields=["organization", "is_supervisor_role"], name="idx_role_org_supervisor"),
        ]

    def __str__(self) -> str:
        if self.is_supervisor_role:
            return f"{self.role_name} [Supervisor] — {self.organization.name}"
        return f"{self.role_name} (Level {self.hierarchy_level}) — {self.organization.name}"

    @property
    def is_supervisor(self) -> bool:
        """Convenience property — True if this is a Supervisor role."""
        return self.is_supervisor_role

    def grants_supervisor_visibility(self) -> bool:
        """True if users of this role can see the entire org."""
        return self.is_supervisor_role or self.has_supervisor_visibility

    def get_permissions_dict(self) -> dict:
        """Returns {permission_key: permission_value} for this role."""
        return {p.permission_key: p.permission_value for p in self.permissions.all()}


# Supervisor role auto-permissions (always granted regardless of RolePermission rows)
SUPERVISOR_AUTO_PERMISSIONS = {
    "can_view_users": True,
    "can_view_dashboards": True,
    "can_view_same_level_roles": True,
    "can_assign_projects": False,
    "can_assign_roads": False,
    "can_create_users": False,
}


class RolePermission(models.Model):
    """
    Key-value permission flags for a Role.

    Standard permission keys:
        can_create_users, can_view_users, can_assign_projects,
        can_assign_roads, can_view_dashboards, can_view_same_level_roles
    """

    PERMISSION_KEYS = [
        "can_create_users",
        "can_view_users",
        "can_assign_projects",
        "can_assign_roads",
        "can_view_dashboards",
        "can_view_same_level_roles",
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="permissions",
        db_index=True,
    )
    permission_key = models.CharField(_("permission key"), max_length=50)
    permission_value = models.BooleanField(_("permission value"), default=False)

    class Meta:
        db_table = "role_permissions"
        verbose_name = _("role permission")
        verbose_name_plural = _("role permissions")
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission_key"],
                name="uq_role_permission_key",
            )
        ]

    def __str__(self) -> str:
        return f"{self.role.role_name} — {self.permission_key}: {self.permission_value}"
