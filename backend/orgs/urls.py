"""
orgs/urls.py
============
App-level URL file for the orgs app.

Primary routing is handled by api/v1/router.py.
This file provides a standalone router for isolated testing.

  /api/v1/organizations/
  /api/v1/hierarchy-levels/
  /api/v1/org-units/
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from orgs.views import HierarchyLevelViewSet, OrganizationViewSet, OrgUnitViewSet

router = DefaultRouter()
router.register(r"organizations",    OrganizationViewSet,    basename="organization")
router.register(r"hierarchy-levels", HierarchyLevelViewSet,  basename="hierarchy-level")
router.register(r"org-units",        OrgUnitViewSet,         basename="org-unit")

app_name = "orgs"

urlpatterns = [
    path("", include(router.urls)),
]
