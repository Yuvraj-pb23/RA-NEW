import sys
with open("accounts/serializers.py", "r") as f:
    content = f.read()

new_code = """        # If NO org_unit_id is provided but role is HO_USER or ORG_ADMIN, auto-link to HO root unit
        if not org_unit_id and user.role in ["HO_USER", "ORG_ADMIN"] and user.organization:
            ho_unit = OrgUnit.objects.filter(organization=user.organization, level__parent_level__isnull=True).first()
            if ho_unit:
                org_unit_id = str(ho_unit.id)

        if org_unit_id:"""

content = content.replace("        if org_unit_id:", new_code, 1)

with open("accounts/serializers.py", "w") as f:
    f.write(content)
print("Patched accounts/serializers.py again")
