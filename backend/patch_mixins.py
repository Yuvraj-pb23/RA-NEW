import re

with open('dashboard/views.py', 'r') as f:
    text = f.read()

# Update mixins block:
# OrgAdminRequiredMixin: SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN
# Since End Users only have access to Dashboard, Projects, Roads, we need to restict users, org_units, hierarchy.
# Projects, Roads can be accessed by all.

mixins_patch = """def check_role(user, allowed_roles):
    role = getattr(user, 'role', None)
    if role not in allowed_roles:
        raise PermissionDenied("You do not have permission to access this page.")

class SuperAdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        check_role(request.user, [SystemRole.SUPER_ADMIN])
        return super().dispatch(request, *args, **kwargs)

class OrgAdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        check_role(request.user, [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN])
        return super().dispatch(request, *args, **kwargs)
"""

old_mixins_pattern = re.compile(r"def check_role\(user, allowed_roles\):.*?class PIURequiredMixin:(?:\s+def dispatch.*?return super\(\)\.dispatch\(request, \*args, \*\*kwargs\))?", re.DOTALL)
text = old_mixins_pattern.sub(mixins_patch, text)

# Now update the Views mixins constraints:
text = text.replace("class OrgUnitListView(RORequiredMixin, DashboardMixin, TemplateView):", "class OrgUnitListView(OrgAdminRequiredMixin, DashboardMixin, TemplateView):")
text = text.replace("class ProjectListView(PIURequiredMixin, DashboardMixin, TemplateView):", "class ProjectListView(DashboardMixin, TemplateView):")
text = text.replace("class RoadListView(DashboardMixin, TemplateView):", "class RoadListView(DashboardMixin, TemplateView):")
text = text.replace("class UserListView(PIURequiredMixin, DashboardMixin, TemplateView):", "class UserListView(OrgAdminRequiredMixin, DashboardMixin, TemplateView):")

with open('dashboard/views.py', 'w') as f:
    f.write(text)

