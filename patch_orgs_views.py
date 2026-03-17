import re

with open("backend/orgs/views.py", "r") as f:
    content = f.read()

# OrganizationViewSet doesn't need much change except removing 'return qs.filter(id=user.organization_id)' duplicates
# But let's check it

# For HierarchyLevelViewSet
hl_replacement = """    def get_queryset(self):
        qs = super().get_queryset()
        from accounts.models import SystemRole
        user = self.request.user
        if user.role == SystemRole.SUPER_ADMIN:
            return qs
        return qs.filter(organization=user.organization)

    def destroy(self, request, *args, **kwargs):"""
content = content.replace("    def destroy(self, request, *args, **kwargs):", hl_replacement, 1)

# For OrgUnitViewSet
ou_replacement = """    def get_queryset(self):
        qs = super().get_queryset()
        from access.utils import get_user_accessible_units
        accessible_units = get_user_accessible_units(self.request.user)
        return qs.filter(id__in=accessible_units.values('id'))

    @action(detail=False, methods=["get"], url_path="tree")"""
content = content.replace('    @action(detail=False, methods=["get"], url_path="tree")', ou_replacement, 1)

with open("backend/orgs/views.py", "w") as f:
    f.write(content)
