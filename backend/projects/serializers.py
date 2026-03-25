"""
projects/serializers.py
=======================
DRF serializers for the Project resource.

ProjectSerializer
  - Full CRUD serializer with read-only display fields.
  - validate() enforces the same two rules as model.clean():
      1. org_unit must be at the 'Project' hierarchy level.
      2. organization must match org_unit.organization.
  - Handles both create and partial-update (PATCH) correctly by
    falling back to instance values when a field is not in the payload.

ProjectMinimalSerializer
  - Lightweight (id + name) for embedding in other serializers.
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    # ── Read-only display fields ───────────────────────────────────────────
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )
    org_unit_name = serializers.CharField(
        source="org_unit.name",
        read_only=True,
    )
    org_unit_level = serializers.CharField(
        source="org_unit.level.level_name",
        read_only=True,
    )
    ho_user_name = serializers.CharField(
        source="ho_user.display_name",
        read_only=True,
    )
    ro_user_name = serializers.CharField(
        source="ro_user.display_name",
        read_only=True,
    )
    piu_user_name = serializers.CharField(
        source="piu_user.display_name",
        read_only=True,
    )
    project_user_name = serializers.CharField(
        source="project_user.display_name",
        read_only=True,
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "organization",
            "organization_name",
            "org_unit",
            "org_unit_name",
            "org_unit_level",
            "ho_user",
            "ho_user_name",
            "ro_user",
            "ro_user_name",
            "piu_user",
            "piu_user_name",
            "project_user",
            "project_user_name",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    # ── Cross-field validation ─────────────────────────────────────────────

    def validate(self, data: dict) -> dict:
        """
        Validate the two core business rules.

        During a PATCH (partial update), fields missing from `data` are
        resolved from the existing instance so the rules can still be
        evaluated on the final state.
        """
        instance = self.instance

        org_unit     = data.get("org_unit",     instance.org_unit     if instance else None)
        organization = data.get("organization", instance.organization  if instance else None)

        errors: dict = {}

        if org_unit is not None:
            # Rule 1: org_unit must be at the "Project" hierarchy level
            level_name = org_unit.level.level_name
            if level_name.lower() != "project":
                errors["org_unit"] = (
                    f"The org unit must belong to the 'Project' hierarchy level "
                    f"(current level: {level_name!r})."
                )

            # Rule 2: organization must match org_unit's organization
            if organization is not None:
                if str(org_unit.organization_id) != str(organization.pk):
                    errors["organization"] = (
                        "The organization must match the org unit's organization."
                    )

        if errors:
            raise ValidationError(errors)

        return data


class ProjectMinimalSerializer(serializers.ModelSerializer):
    """Lightweight serializer for embedding a project reference."""

    class Meta:
        model = Project
        fields = ["id", "name"]
