"""
access/serializers.py
=====================
Serializers for UserOrgAccess CRUD.

UserOrgAccessSerializer
  - Used for all responses (list, create, retrieve).
  - Includes nested read-only display fields.
  - validate() enforces both model.clean() rules:
      1. Non-admin role must match the org unit's hierarchy level name.
      2. Admin role must only be assigned to root-level OrgUnits.
  - Duplicate check: prevents creating a second access record for the
    same (user, org_unit) pair (returns 400 with clear message).

UserOrgAccessWriteSerializer
  - Slim write-only fields for POST body.
"""

from rest_framework import serializers

from .models import UserOrgAccess


class UserOrgAccessSerializer(serializers.ModelSerializer):
    # ── Read-only display fields ───────────────────────────────────────────
    user_email        = serializers.EmailField(source="user.email",         read_only=True)
    user_name         = serializers.CharField(source="user.get_full_name",  read_only=True)
    org_unit_name     = serializers.CharField(source="org_unit.name",       read_only=True)
    org_unit_level    = serializers.CharField(source="org_unit.level.level_name", read_only=True)
    organization_id   = serializers.UUIDField(source="org_unit.organization.id",   read_only=True)
    organization_name = serializers.CharField(source="org_unit.organization.name", read_only=True)
    role_display      = serializers.CharField(source="get_role_display",    read_only=True)

    class Meta:
        model  = UserOrgAccess
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "org_unit",
            "org_unit_name",
            "org_unit_level",
            "organization_id",
            "organization_name",
            "role",
            "role_display",
            "is_active",
            "assigned_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "assigned_by",
            "created_at",
            "updated_at",
        ]

    # ── Cross-field validation ─────────────────────────────────────────────

    def validate(self, data: dict) -> dict:
        """
        Enforce business rules via model.clean() and check for duplicates.
        """
        instance = self.instance

        user     = data.get("user",     instance.user     if instance else None)
        org_unit = data.get("org_unit", instance.org_unit if instance else None)
        role     = data.get("role",     instance.role     if instance else None)

        # ── Duplicate check (create only) ─────────────────────────────────
        if not instance and user and org_unit:
            if UserOrgAccess.objects.filter(user=user, org_unit=org_unit).exists():
                raise serializers.ValidationError(
                    {
                        "non_field_errors": (
                            "An access record for this user and org unit already "
                            "exists. Use PATCH to update the role."
                        )
                    }
                )

        # ── Model-level rules (role ↔ level_name, admin ↔ root) ───────────
        if role and org_unit:
            # Load level and parent lazily — already available from select_related
            level_name = org_unit.level.level_name.lower()
            role_lower = role.lower()

            if role_lower != "admin" and role_lower != level_name:
                raise serializers.ValidationError(
                    {
                        "role": (
                            f"Role '{role}' does not match the org unit's "
                            f"hierarchy level '{org_unit.level.level_name}'. "
                            f"Expected role: '{level_name}'."
                        )
                    }
                )

            if role_lower == "admin" and org_unit.parent_unit is not None:
                raise serializers.ValidationError(
                    {
                        "role": (
                            f"Admin role must only be assigned to root-level "
                            f"units. '{org_unit.name}' is not a root unit."
                        )
                    }
                )

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["assigned_by"] = request.user
        return super().create(validated_data)
