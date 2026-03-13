"""
roads/urls.py
=============
URL configuration for the roads app.

Registered routes (relative to mount point /api/roads/):
  GET    /             -> road-list
  POST   /             -> road-list   (create)
  GET    /{id}/        -> road-detail
  PUT    /{id}/        -> road-detail (full update)
  PATCH  /{id}/        -> road-detail (partial update)
  DELETE /{id}/        -> road-detail (destroy)
"""

from rest_framework.routers import DefaultRouter

from .views import RoadViewSet

router = DefaultRouter()
router.register(r"", RoadViewSet, basename="road")

urlpatterns = router.urls
