import re

with open('accounts/views.py', 'r') as f:
    text = f.read()

# Replace:
#    def get_permissions(self):
#        if self.action in ("list", "create", "destroy"):
#            return [IsAuthenticated(), IsAdminRole()]
#        # retrieve, update, partial_update, me, set_password → self or admin
#        return [IsAuthenticated(), IsSelfOrAdmin()]

old_perm = '''    def get_permissions(self):
        if self.action in ("list", "create", "destroy"):
            return [IsAuthenticated(), IsAdminRole()]
        # retrieve, update, partial_update, me, set_password → self or admin
        return [IsAuthenticated(), IsSelfOrAdmin()]'''

new_perm = '''    def get_permissions(self):
        if self.action in ("list", "create"):
            # Any authenticated user except PROJECT_USER can access list/create 
            return [IsAuthenticated()]
        if self.action == "destroy":
            return [IsAuthenticated(), IsAdminRole()]
        # retrieve, update, partial_update, me, set_password → self or admin
        return [IsAuthenticated(), IsSelfOrAdmin()]'''

if old_perm in text:
    text = text.replace(old_perm, new_perm)
    with open('accounts/views.py', 'w') as f:
        f.write(text)
    print("Patched get_permissions")
else:
    print("Could not find get_permissions block")

