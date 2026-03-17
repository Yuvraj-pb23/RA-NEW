from rest_framework.routers import DefaultRouter
from accounts.views import UserViewSet
from orgs.views import HierarchyLevelViewSet, OrganizationViewSet, OrgUnitViewSet
from projects.views import ProjectViewSet
from roads.views import RoadViewSet
from access.views import UserOrgAccessViewSet

router = DefaultRouter()

router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'hierarchy-levels', HierarchyLevelViewSet, basename='hierarchy-level')
router.register(r'org-units', OrgUnitViewSet, basename='org-unit')
router.register(r'users', UserViewSet, basename='user')

# -- Projects, Roads, Access --------------------------------------------------
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"roads", RoadViewSet, basename="road")
router.register(r"user-access", UserOrgAccessViewSet, basename="user-access")
