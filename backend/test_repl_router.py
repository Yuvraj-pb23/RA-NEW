import re
with open("api/v1/router.py", "r") as f:
    text = f.read()

text = text.replace(
    'from accounts.views import UserViewSet\nfrom orgs.views import HierarchyLevelViewSet, OrganizationViewSet, OrgUnitViewSet',
    'from accounts.views import UserViewSet\nfrom orgs.views import HierarchyLevelViewSet, OrganizationViewSet, OrgUnitViewSet\nfrom projects.views import ProjectViewSet\nfrom roads.views import RoadViewSet\nfrom access.views import UserOrgAccessViewSet'
)

new_routes = """
# -- Projects, Roads, Access --------------------------------------------------
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"roads", RoadViewSet, basename="road")
router.register(r"user-access", UserOrgAccessViewSet, basename="user-access")
"""

text = text + new_routes

with open("api/v1/router.py", "w") as f:
    f.write(text)
