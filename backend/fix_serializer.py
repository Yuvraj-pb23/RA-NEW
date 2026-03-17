import sys

with open("orgs/serializers.py", "r") as f:
    content = f.read()

old_code = """        if request and getattr(request.user, "role", None) != "SUPER_ADMIN":
            from access.utils import get_user_accessible_units
            accessible = get_user_accessible_units(request.user)
                
            if parent and parent.id not in accessible:
                raise serializers.ValidationError({"parent_unit": "You do not have access to create a unit under this parent."})"""

new_code = """        if request and getattr(request.user, "role", None) != "SUPER_ADMIN":
            from access.utils import get_user_accessible_units
            accessible_units = get_user_accessible_units(request.user)
                
            if parent and not accessible_units.filter(id=parent.id).exists():
                raise serializers.ValidationError({"parent_unit": "You do not have access to create a unit under this parent."})"""

if old_code in content:
    with open("orgs/serializers.py", "w") as f:
        f.write(content.replace(old_code, new_code))
    print("Fixed serializers.py")
else:
    print("Could not find old code in serializers.py!")

