"""
roles/serializers.py
====================
Serializers for Role and RolePermission models.

Two role types:
  - Hierarchy Role: requires hierarchy_level (and optional parent_role)
  - Supervisor Role: is_supervisor_role=True, no hierarchy_level/parent_role,
    auto-granted org-wide visibility permissions
"""
from rest_framework import serializers
from .models import Role, RolePermission, SUPERVISOR_AUTO_PERMISSIONS


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ["id", "permission_key", "permission_value"]


class RoleSerializer(serializers.ModelSerializer):
    """Full role serializer including nested permissions — used for GET."""
    permissions = RolePermissionSerializer(many=True, read_only=True)
    parent_role_name = serializers.CharField(
        source="parent_role.role_name", read_only=True, default=None
    )
    created_by_name = serializers.CharField(
        source="created_by.display_name", read_only=True, default=None
    )
    # Flat permission booleans for easy frontend consumption
    can_create_users = serializers.SerializerMethodField()
    can_view_users = serializers.SerializerMethodField()
    can_assign_projects = serializers.SerializerMethodField()
    can_assign_roads = serializers.SerializerMethodField()
    can_view_dashboards = serializers.SerializerMethodField()
    can_view_same_level_roles = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id",
            "organization",
            "role_name",
            "is_supervisor_role",
            "hierarchy_level",
            "parent_role",
            "parent_role_name",
            "has_supervisor_visibility",
            "status",
            "created_by",
            "created_by_name",
            "created_at",
            "permissions",
            "can_create_users",
            "can_view_users",
            "can_assign_projects",
            "can_assign_roads",
            "can_view_dashboards",
            "can_view_same_level_roles",
        ]
        read_only_fields = ["id", "created_by", "created_at"]

    def _get_perm(self, obj, key):
        # Supervisor roles always have auto-permissions regardless of DB rows
        if obj.is_supervisor_role:
            return SUPERVISOR_AUTO_PERMISSIONS.get(key, False)
        perm = obj.permissions.filter(permission_key=key).first()
        return perm.permission_value if perm else False

    def get_can_create_users(self, obj): return self._get_perm(obj, "can_create_users")
    def get_can_view_users(self, obj): return self._get_perm(obj, "can_view_users")
    def get_can_assign_projects(self, obj): return self._get_perm(obj, "can_assign_projects")
    def get_can_assign_roads(self, obj): return self._get_perm(obj, "can_assign_roads")
    def get_can_view_dashboards(self, obj): return self._get_perm(obj, "can_view_dashboards")
    def get_can_view_same_level_roles(self, obj): return self._get_perm(obj, "can_view_same_level_roles")


class RoleCreateUpdateSerializer(serializers.ModelSerializer):
    """Used for POST/PUT/PATCH — accepts permission booleans as flat fields."""
    can_create_users = serializers.BooleanField(required=False, default=False)
    can_view_users = serializers.BooleanField(required=False, default=False)
    can_assign_projects = serializers.BooleanField(required=False, default=False)
    can_assign_roads = serializers.BooleanField(required=False, default=False)
    can_view_dashboards = serializers.BooleanField(required=False, default=False)
    can_view_same_level_roles = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = Role
        fields = [
            "role_name",
            "is_supervisor_role",
            "hierarchy_level",
            "parent_role",
            "has_supervisor_visibility",
            "status",
            "can_create_users",
            "can_view_users",
            "can_assign_projects",
            "can_assign_roads",
            "can_view_dashboards",
            "can_view_same_level_roles",
        ]

    def validate(self, attrs):
        is_supervisor = attrs.get(
            "is_supervisor_role",
            getattr(self.instance, "is_supervisor_role", False)
        )

        if not is_supervisor:
            # Hierarchy roles MUST have hierarchy_level
            level = attrs.get(
                "hierarchy_level",
                getattr(self.instance, "hierarchy_level", None)
            )
            if not level:
                raise serializers.ValidationError(
                    {"hierarchy_level": "Hierarchy level is required for non-supervisor roles."}
                )

            # Parent role must have a lower level number (= higher authority)
            parent = attrs.get("parent_role")
            if parent and level and parent.hierarchy_level is not None:
                if parent.hierarchy_level >= level:
                    raise serializers.ValidationError(
                        {"parent_role": "Parent role must have a lower hierarchy level number (higher authority)."}
                    )
        else:
            # Supervisor roles: clear hierarchy fields
            attrs["hierarchy_level"] = None
            attrs["parent_role"] = None
            # Supervisor roles implicitly have supervisor visibility
            attrs["has_supervisor_visibility"] = True

        return attrs

    def validate_parent_role(self, value):
        """Ensure parent_role belongs to the same org."""
        if value is None:
            return value
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            org = request.user.organization
            if org and value.organization_id != org.id:
                raise serializers.ValidationError(
                    "Parent role must belong to the same organization."
                )
            # Parent cannot be a supervisor role
            if value.is_supervisor_role:
                raise serializers.ValidationError(
                    "A supervisor role cannot be used as a parent role in the hierarchy."
                )
        return value

    def _save_permissions(self, role, perm_data):
        """Persist permission rows. Supervisor roles get auto-permissions."""
        if role.is_supervisor_role:
            # Store auto-permissions explicitly
            for key, value in SUPERVISOR_AUTO_PERMISSIONS.items():
                RolePermission.objects.update_or_create(
                    role=role, permission_key=key,
                    defaults={"permission_value": value},
                )
        else:
            for key, value in perm_data.items():
                RolePermission.objects.update_or_create(
                    role=role, permission_key=key,
                    defaults={"permission_value": value},
                )

    def create(self, validated_data):
        request = self.context.get("request")
        perm_keys = [
            "can_create_users", "can_view_users", "can_assign_projects",
            "can_assign_roads", "can_view_dashboards", "can_view_same_level_roles",
        ]
        perm_data = {k: validated_data.pop(k, False) for k in perm_keys}

        role = Role.objects.create(
            organization=request.user.organization,
            created_by=request.user,
            **validated_data,
        )
        self._save_permissions(role, perm_data)
        return role

    def update(self, instance, validated_data):
        perm_keys = [
            "can_create_users", "can_view_users", "can_assign_projects",
            "can_assign_roads", "can_view_dashboards", "can_view_same_level_roles",
        ]
        perm_data = {k: validated_data.pop(k, None) for k in perm_keys if k in validated_data}

        # Apply field updates
        instance = super().update(instance, validated_data)

        if perm_data:
            self._save_permissions(instance, perm_data)
        elif instance.is_supervisor_role:
            # Always re-enforce supervisor auto-perms on update
            self._save_permissions(instance, {})

        return instance


class RoleMinimalSerializer(serializers.ModelSerializer):
    """Tiny read-only snapshot for dropdowns."""
    class Meta:
        model = Role
        fields = [
            "id", "role_name", "is_supervisor_role",
            "hierarchy_level", "parent_role",
            "has_supervisor_visibility", "status"
        ]
