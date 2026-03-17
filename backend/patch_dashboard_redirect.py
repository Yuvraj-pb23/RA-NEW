import re

with open("dashboard/views.py", "r") as f:
    text = f.read()

# Add redirect import if not exists
if "from django.shortcuts import redirect" not in text:
    text = text.replace("from django.views.generic import TemplateView", "from django.views.generic import TemplateView\nfrom django.shortcuts import redirect")

# Replace check_role and mixins
new_mixins = """def check_role(user, allowed_roles):
    role = getattr(user, 'role', None)
    return role in allowed_roles

class SuperAdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not check_role(request.user, [SystemRole.SUPER_ADMIN]):
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)

class OrgAdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not check_role(request.user, [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]):
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)"""

text = re.sub(
    r"def check_role\(user, allowed_roles\):.*?return super\(\)\.dispatch\(request, \*args, \*\*kwargs\)",
    new_mixins,
    text,
    flags=re.DOTALL
)

with open("dashboard/views.py", "w") as f:
    f.write(text)

print("done")
