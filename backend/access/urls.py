"""
access/urls.py
==============
Standalone URL configuration for the access app.

Mounted at /api/user-access/ in config/urls.py.

Routes:
  GET    /             -> user-access-list
  POST   /             -> user-access-list    (create)
  GET    /{id}/        -> user-access-detail
  DELETE /{id}/        -> user-access-detail  (destroy)
  GET    /by-org-unit/ -> by-org-unit action
  GET    /my/          -> my action
"""

from rest_framework.routers import DefaultRouter

from .views import UserOrgAccessViewSet

router = DefaultRouter()
router.register(r"", UserOrgAccessViewSet, basename="user-access")

urlpatterns = router.urls
