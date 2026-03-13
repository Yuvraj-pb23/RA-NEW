"""
api/v1/router.py
=================
Central DRF router for API v1.

All ViewSets are registered here and nowhere else.
This module is imported by api/urls.py.

Registered prefixes
-------------------
  organizations      -> OrganizationViewSet
  hierarchy-levels   -> HierarchyLevelViewSet
  org-units          -> OrgUnitViewSet
  users              -> UserViewSet
  user-access        -> UserOrgAccessViewSet

Note: projects, roads, and user-access are standalone apps mounted at
  /api/projects/  /api/roads/  /api/user-access/  (see config/urls.py).
"""
from rest_framework.routers import DefaultRouter

from accounts.views import UserViewSet
from orgs.views import HierarchyLevelViewSet, OrganizationViewSet, OrgUnitViewSet
from projects.views import ProjectViewSet
from roads.views import RoadViewSet
from access.views import UserOrgAccessViewSet

router = DefaultRouter()

# -- Organizations & hierarchy ------------------------------------------------
router.register(
    r"organizations",
    OrganizationViewSet,
    basename="organization",
)
router.register(
    r"hierarchy-levels",
    HierarchyLevelViewSet,
    basename="hierarchy-level",
)
router.register(
    r"org-units",
    OrgUnitViewSet,
    basename="org-unit",
)

# -- Users --------------------------------------------------------------------
router.register(
    r"users",
    UserViewSet,
    basename="user",
)

# -- Projects, Roads, Access --------------------------------------------------
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"roads", RoadViewSet, basename="road")
router.register(r"user-access", UserOrgAccessViewSet, basename="user-access")
