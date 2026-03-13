from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from orgs.models import OrgUnit


# =============================================================================
# UserOrgAccess
# =============================================================================

class UserOrgAccess(BaseModel):
    """
    Assigns a user to an OrgUnit with a specific role.

    Rules
    -----
    - One role per (user, org_unit) pair — UNIQUE constraint.
    - Admin role should only be assigned to root-level (top) OrgUnits.
    - is_active=False soft-disables access without losing the record.

    Role hierarchy (broadest to narrowest access)
    ----------------------------------------------
    ADMIN   -> platform-wide: all organizations and all roads
    HO      -> HO unit and every unit below it
    RO      -> RO unit and every unit below it
    PIU     -> PIU unit and every unit below it
    PROJECT -> only the directly assigned project unit
    """

    class RoleChoices(models.TextChoices):
        ADMIN   = "admin",   _("Admin")
        HO      = "ho",      _("HO")
        RO      = "ro",      _("RO")
        PIU     = "piu",     _("PIU")
        PROJECT = "project", _("Project")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="org_accesses",
        db_index=True,
        help_text=_("The user being granted access."),
    )
    org_unit = models.ForeignKey(
        OrgUnit,
        on_delete=models.CASCADE,
        related_name="user_accesses",
        db_index=True,
        help_text=_("The OrgUnit this user is assigned to."),
    )
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=RoleChoices.choices,
        db_index=True,
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_assignments_made",
        help_text=_("The admin who created this assignment (audit trail)."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        db_index=True,
        help_text=_("Soft-disable access without deleting the record."),
    )

    class Meta:
        db_table = "access_userorgaccess"
        verbose_name = _("user org access")
        verbose_name_plural = _("user org accesses")
        ordering = ["user", "org_unit"]
        indexes = [
            models.Index(
                fields=["user", "is_active"],
                name="idx_access_user_active",
            ),
            models.Index(
                fields=["org_unit", "role"],
                name="idx_access_unit_role",
            ),
            models.Index(
                fields=["role"],
                name="idx_access_role",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "org_unit"],
                name="uq_access_user_orgunit",
            )
        ]

    def __str__(self) -> str:
        return (
            f"{self.user} -> {self.org_unit.name} "
            f"[{self.get_role_display()}]"
        )

    def clean(self) -> None:
        """
        Validation rules:
        1. Non-admin roles must match the org unit's hierarchy level name
           (case-insensitive):
             role='ho'      -> level_name must be 'HO'
             role='ro'      -> level_name must be 'RO'
             role='piu'     -> level_name must be 'PIU'
             role='project' -> level_name must be 'Project'
        2. Admin role must only be assigned to root-level OrgUnits
           (parent_unit is None).
        """
        errors: dict = {}

        if self.role and self.org_unit_id:
            level_name = self.org_unit.level.level_name.lower()
            role_lower = self.role.lower()

            # Rule 1: non-admin roles must match the unit's level name
            if role_lower != "admin" and role_lower != level_name:
                errors["role"] = _(
                    "Role '%(role)s' does not match the org unit's hierarchy "
                    "level '%(level)s'."
                ) % {"role": self.role, "level": self.org_unit.level.level_name}

            # Rule 2: admin only on root units
            if (
                role_lower == "admin"
                and self.org_unit.parent_unit is not None
            ):
                errors["role"] = _(
                    "Admin role should only be assigned to root-level units. "
                    "'%(unit)s' is not a root unit."
                ) % {"unit": self.org_unit.name}

        if errors:
            raise ValidationError(errors)

    # ── Class-level helpers ────────────────────────────────────────────────

    @property
    def organization(self):
        """Convenience accessor — avoid in bulk queries."""
        return self.org_unit.organization

    @classmethod
    def get_user_roles(cls, user) -> dict:
        """
        Returns {org_unit_id: role} for a user's active assignments.
        Single query. Used by permission classes.
        """
        return dict(
            cls.objects.filter(user=user, is_active=True)
            .values_list("org_unit_id", "role")
        )
