import re

with open('dashboard/views.py', 'r') as f:
    text = f.read()

# Fix repeated OrgAdminRequiredMixin
text = re.sub(r'(class OrgAdminRequiredMixin:.*?return super\(\)\.dispatch\(request, \*args, \*\*kwargs\)\n+)+', 
'''class OrgAdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not check_role(request.user, [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN, SystemRole.HO_USER]):
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)

''', text, flags=re.DOTALL)

# Update get_context_data in both places
text = text.replace('SystemRole.ORG_ADMIN]', 'SystemRole.ORG_ADMIN, SystemRole.HO_USER]')

with open('dashboard/views.py', 'w') as f:
    f.write(text)

