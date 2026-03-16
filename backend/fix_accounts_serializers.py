import re

with open("accounts/serializers.py", "r") as f:
    text = f.read()

# Fix the broken `read_only_fields` block in `UserSerializer` that was placed after `get_assigned_unit`.

text = text.replace("""        return None

        read_only_fields = [
            "id",
            "is_staff",
            "date_joined",
            "updated_at",
            "display_name",
            "is_platform_admin",
        ]""", """        return None""")

# Add read_only_fields back to UserSerializer Meta class
text = text.replace("""            "assigned_unit",
        ]

    def get_assigned_unit(self, obj):""", """            "assigned_unit",
        ]
        read_only_fields = [
            "id",
            "is_staff",
            "date_joined",
            "updated_at",
            "display_name",
            "is_platform_admin",
        ]

    def get_assigned_unit(self, obj):""")

# Update UserCreateSerializer's create to include assigned_by
def_create_replacement = """    def create(self, validated_data):
        from access.models import UserOrgAccess
        from orgs.models import OrgUnit
        
        password = validated_data.pop("password")
        org_unit_id = validated_data.pop("org_unit", None)
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
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
            
        return user"""

text = re.sub(r'    def create\(self, validated_data\):.*?return user', def_create_replacement, text, flags=re.DOTALL)

with open("accounts/serializers.py", "w") as f:
    f.write(text)

