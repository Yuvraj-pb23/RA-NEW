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
        
        level = attrs.get('level') or getattr(instance, 'level', None)
        parent = attrs.get('parent_unit') or getattr(instance, 'parent_unit', None)
        organization = attrs.get('organization') or getattr(instance, 'organization', None)

        if organization and level:
            if getattr(level, 'parent_level', None) is None:
                if parent is not None:
                    raise serializers.ValidationError({"parent_unit": "Root level units cannot have a parent unit."})
                
                root_units_count = OrgUnit.objects.filter(
                    organization=organization, 
                    level__parent_level__isnull=True
                ).exclude(pk=instance.pk).count()
                
                if root_units_count > 0:
                    raise serializers.ValidationError({"level": "Only one root unit can exist per organization."})
            else:
                if not parent:
                    raise serializers.ValidationError({"parent_unit": "Parent unit must be provided for non-root units."})
                
                if parent.level != level.parent_level:
                    raise serializers.ValidationError({
                        "parent_unit": f"Parent unit must belong to the {level.parent_level.level_name} level."
                    })

        # Hierarchy access check for non-superadmins
        if request and getattr(request.user, "role", None) != "SUPER_ADMIN":
            from access.utils import get_user_accessible_units
            accessible = get_user_accessible_units(request.user)
                
            if parent and parent.id not in accessible:
                raise serializers.ValidationError({"parent_unit": "You do not have access to create a unit under this parent."})
                
        return attrs
'''

# Find def validate block and replace it
text = re.sub(r'    def validate\(self, attrs\):\n        instance = self\.instance or OrgUnit\(\).*?(?=\n\n    class Meta:|\n\nclass OrgUnitTreeSerializer)', replacement, text, flags=re.DOTALL)

with open('orgs/serializers.py', 'w') as f:
    f.write(text)
