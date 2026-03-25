"""
projects/models.py
==================
Defines the Project model.

A Project is a unit of work assigned to an OrgUnit that sits at the
"Project" level in the organization's hierarchy.

Rules enforced:
  1. The OrgUnit must be at the HierarchyLevel whose level_name == "Project"
     (case-insensitive). This ensures projects are always attached to the
     correct tier of the tree.
  2. The `organization` field must match the OrgUnit's own organization,
     preventing cross-org assignment.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from orgs.models import Organization, OrgUnit


from django.conf import settings

class Project(BaseModel):
    """
    A single project, scoped to one org unit at the 'Project' hierarchy level.

    Inherits from BaseModel:
      - id          UUIDField  (primary key, auto-generated)
      - created_at  DateTimeField (auto_now_add)
      - updated_at  DateTimeField (auto_now)
    """

    name = models.CharField(
        _("project name"),
        max_length=255,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="org_projects",
        db_index=True,
        help_text=_("The organization this project belongs to."),
    )
    org_unit = models.ForeignKey(
        OrgUnit,
        on_delete=models.CASCADE,
        related_name="org_unit_projects",
        db_index=True,
        null=True,
        blank=True,
        help_text=_(
            "The org unit executing this project. "
            "Must be at the 'Project' hierarchy level."
        ),
    )
    ho_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="projects_as_ho",
        db_index=True,
        null=True,
        blank=True,
        help_text=_("The assigned HO user."),
    )
    ro_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="projects_as_ro",
        db_index=True,
        null=True,
        blank=True,
        help_text=_("The assigned RO user."),
    )
    piu_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="projects_as_piu",
        db_index=True,
        null=True,
        blank=True,
        help_text=_("The assigned PIU user."),
    )
    project_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="projects_as_project_user",
        db_index=True,
        null=True,
        blank=True,
        help_text=_("The assigned Project user."),
    )
    description = models.TextField(
        _("description"),
        blank=True,
        default="",
    )

    class Meta:
        db_table = "projects_project"
        verbose_name = _("project")
        verbose_name_plural = _("projects")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization"], name="idx_projects_org"),
            models.Index(fields=["org_unit"],     name="idx_projects_orgunit"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uq_project_org_name",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        """
        Model-level validation.

        Rule 1 — OrgUnit must be at the "Project" hierarchy level.
        Rule 2 — Organization must match the OrgUnit's organization.
        """
        errors: dict = {}

        if self.org_unit_id:
            # Rule 1: hierarchy level name must be "Project" (case-insensitive)
            level_name = self.org_unit.level.level_name
            if level_name.lower() != "project":
                errors["org_unit"] = _(
                    "The org unit must belong to the 'Project' hierarchy level "
                    "(current level: %(level)s)."
                ) % {"level": level_name}

            # Rule 2: organization must match
            if self.organization_id:
                if str(self.org_unit.organization_id) != str(self.organization_id):
                    errors["organization"] = _(
                        "The organization must match the org unit's organization."
                    )

        if errors:
            raise ValidationError(errors)
