import sys

with open("orgs/serializers.py", "r") as f:
    content = f.read()

old_code = """        # Hierarchy access check for non-superadmins
        if request and getattr(request.user, "role", None) != "SUPER_ADMIN":
            from access.utils import get_user_accessible_units
            accessible_units = get_user_accessible_units(request.user)
                
            if parent and not accessible_units.filter(id=parent.id).exists():
                raise serializers.ValidationError({"parent_unit": "You do not have access to create a unit under this parent."})"""

new_code = """        # Hierarchy access check for non-superadmins
        if request and getattr(request.user, "role", None) != "SUPER_ADMIN":
            from access.utils import get_descendant_units
            
            # Get user's primary assigned org unit
            user_access = request.user.org_accesses.filter(is_active=True).first()
            if not user_access:
                raise serializers.ValidationError({"parent_unit": "You are not assigned to any org unit."})
                
            user_org_unit = user_access.org_unit
            accessible_units = get_descendant_units(user_org_unit)
                
            if parent and not accessible_units.filter(id=parent.id).exists():
                raise serializers.ValidationError({"parent_unit": "You do not have access to create a unit under this parent."})"""

if old_code in content:
    with open("orgs/serializers.py", "w") as f:
        f.write(content.replace(old_code, new_code))
    print("Fixed serializers.py")
else:
    print("Could not find old code in serializers.py!")
