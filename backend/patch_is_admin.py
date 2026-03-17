import re

with open('access/permissions.py', 'r') as f:
    content = f.read()

new_is_admin = """def is_admin(user) -> bool:
    \"\"\"Returns True if user has any admin-role assignment.\"\"\"
    if user.is_superuser:
        return True
    return user.role in ['SUPER_ADMIN', 'ORG_ADMIN', 'HO_USER']"""

content = re.sub(r'def is_admin\(user\) -> bool:.*?return user\.role in \[\'SUPER_ADMIN\', \'ORG_ADMIN\'\]', new_is_admin, content, flags=re.DOTALL)

with open('access/permissions.py', 'w') as f:
    f.write(content)

# Update core/permissions.py too
with open('core/permissions.py', 'r') as f:
    content = f.read()
content = content.replace("SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]", "SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN, SystemRole.HO_USER]")
with open('core/permissions.py', 'w') as f:
    f.write(content)
