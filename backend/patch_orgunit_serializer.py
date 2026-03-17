import re

with open('orgs/serializers.py', 'r') as f:
    text = f.read()

replacement = '''
    def validate(self, attrs):
        instance = self.instance or OrgUnit()
        for attr, value in attrs.items():
            setattr(instance, attr, value)
        instance.clean()

        request = self.context.get("request")
        if request and request.user.role != "SUPER_ADMIN":
            from access.utils import get_user_accessible_units
            accessible = get_user_accessible_units(request.user)
            parent = attrs.get('parent_unit') or getattr(instance, 'parent_unit', None)
            
            if not parent:
                raise serializers.ValidationError({"parent_unit": "Non-superadmins must specify a parent unit."})
                
            if parent.id not in accessible:
                raise serializers.ValidationError({"parent_unit": "You do not have access to create a unit under this parent."})
                
        return attrs'''

text = re.sub(r'    def validate\(self, attrs\):\n        instance = self\.instance or OrgUnit\(\)\n        for attr, value in attrs\.items\(\):\n            setattr\(instance, attr, value\)\n        instance\.clean\(\)\n        return attrs', replacement, text)

with open('orgs/serializers.py', 'w') as f:
    f.write(text)

