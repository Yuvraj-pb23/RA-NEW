from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Tiny read-only snapshot of a User.
    Used as a nested field inside other serializers (e.g., assigned_by).
    Never exposes password or sensitive fields.
    """

    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "display_name"]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """
    Full user profile — used on GET /api/v1/users/<id>/ and GET /api/v1/auth/me/.
    """

    display_name = serializers.CharField(read_only=True)
    is_platform_admin = serializers.BooleanField(read_only=True)
    assigned_unit = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "display_name",
            "is_platform_admin",
            "is_active",
            "is_staff",
            "date_joined",
            "updated_at",
            "role",
            "organization",
            "assigned_unit",
        ]
        read_only_fields = [
            "id",
            "is_staff",
            "date_joined",
            "updated_at",
            "display_name",
            "is_platform_admin",
        ]

    def get_assigned_unit(self, obj):
        from access.models import UserOrgAccess
        # return a dict of {id, name, level_name} for the first active access
        acc = obj.org_accesses.filter(is_active=True).select_related('org_unit', 'org_unit__level').first()
        if acc:
            return {
                "id": acc.org_unit.id,
                "name": acc.org_unit.name,
                "level_name": acc.org_unit.level.level_name
            }
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Used by POST /api/v1/users/ (admin creates a new user).
    Accepts plain-text password and hashes it via set_password().
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    org_unit = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["email", "full_name", "phone", "password", "password_confirm", "role", "organization", "org_unit"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
            
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return attrs
            
        current_user = request.user
        new_role = attrs.get("role")
        
        # 1. Validate Role Hierarchy
        ROLE_HIERARCHY = {
            "SUPER_ADMIN": 1,
            "ORG_ADMIN": 2,
            "HO_USER": 3,
            "RO_USER": 4,
            "PIU_USER": 5,
            "PROJECT_USER": 6,
        }
        
        current_weight = ROLE_HIERARCHY.get(current_user.role, 6)
        new_weight = ROLE_HIERARCHY.get(new_role, 6)
        
        if current_weight >= new_weight:
            raise serializers.ValidationError(
                {"role": "You can only create users with a role below your own hierarchy level."}
            )

        # 2. Validate Org Unit Hierarchy
        org_unit_id = attrs.get("org_unit")
        if new_role not in ["SUPER_ADMIN", "ORG_ADMIN"] and org_unit_id:
            if current_user.role != "SUPER_ADMIN":
                from access.utils import get_user_accessible_units
                try:
                    from orgs.models import OrgUnit
                    target_unit = OrgUnit.objects.get(id=org_unit_id)
                except Exception:
                    raise serializers.ValidationError({"org_unit": "Invalid org unit."})
                
                accessible_units = get_user_accessible_units(current_user)
                if not accessible_units.filter(id=target_unit.id).exists():
                    raise serializers.ValidationError({"org_unit": "Assigned org unit must be a child of your assigned org unit."})
        
        return attrs

    def create(self, validated_data):
        from access.models import UserOrgAccess
        from orgs.models import OrgUnit
        
        password = validated_data.pop("password")
        org_unit_id = validated_data.pop("org_unit", None)
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # If NO org_unit_id is provided but role is HO_USER or ORG_ADMIN, auto-link to HO root unit
        if not org_unit_id and user.role in ["HO_USER", "ORG_ADMIN"] and user.organization:
            ho_unit = OrgUnit.objects.filter(organization=user.organization, level__parent_level__isnull=True).first()
            if ho_unit:
                org_unit_id = str(ho_unit.id)

        # If NO org_unit_id is provided but role is HO_USER or ORG_ADMIN, auto-link to HO root unit
        if not org_unit_id and user.role in ["HO_USER", "ORG_ADMIN"] and user.organization:
            ho_unit = OrgUnit.objects.filter(organization=user.organization, level__parent_level__isnull=True).first()
            if ho_unit:
                org_unit_id = str(ho_unit.id)

        # If NO org_unit_id is provided but role is HO_USER or ORG_ADMIN, auto-link to HO root unit
        if not org_unit_id and user.role in ["HO_USER", "ORG_ADMIN"] and user.organization:
            ho_unit = OrgUnit.objects.filter(organization=user.organization, level__parent_level__isnull=True).first()
            if ho_unit:
                org_unit_id = str(ho_unit.id)

        # If NO org_unit_id is provided but role is HO_USER or ORG_ADMIN, auto-link to HO root unit
        if not org_unit_id and user.role in ["HO_USER", "ORG_ADMIN"] and user.organization:
            ho_unit = OrgUnit.objects.filter(organization=user.organization, level__parent_level__isnull=True).first()
            if ho_unit:
                org_unit_id = str(ho_unit.id)

        # If NO org_unit_id is provided but role is HO_USER or ORG_ADMIN, auto-link to HO root unit
        if not org_unit_id and user.role in ["HO_USER", "ORG_ADMIN"] and user.organization:
            ho_unit = OrgUnit.objects.filter(organization=user.organization, level__parent_level__isnull=True).first()
            if ho_unit:
                org_unit_id = str(ho_unit.id)

        # If NO org_unit_id is provided but role is HO_USER or ORG_ADMIN, auto-link to HO root unit
        if not org_unit_id and user.role in ["HO_USER", "ORG_ADMIN"] and user.organization:
            ho_unit = OrgUnit.objects.filter(organization=user.organization, level__parent_level__isnull=True).first()
            if ho_unit:
                org_unit_id = str(ho_unit.id)

        if org_unit_id:
            try:
                ou = OrgUnit.objects.get(id=org_unit_id)
                # Map system role to UserOrgAccess role
                role_map = {
                    "SUPER_ADMIN": "admin",
                    "ORG_ADMIN": "admin",
                    "HO_USER": "ho",
                    "RO_USER": "ro",
                    "PIU_USER": "piu",
                    "PROJECT_USER": "project"
                }
                acc_role = role_map.get(user.role, "project")
                request = self.context.get("request")
                assigned_by = request.user if request and hasattr(request, "user") else None
                
                UserOrgAccess.objects.create(
                    user=user,
                    org_unit=ou,
                    role=acc_role,
                    assigned_by=assigned_by,
                    is_active=True
                )
            except OrgUnit.DoesNotExist:
                pass
            
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Used by PATCH /api/v1/users/<id>/.
    Cannot change email or password through this serializer.
    Password change gets its own dedicated endpoint.
    """

    class Meta:
        model = User
        fields = ["full_name", "phone", "is_active"]
