"""
projects/urls.py
================
URL configuration for the projects app.

Registered routes (relative to mount point /api/projects/):
  GET    /             → project-list
  POST   /             → project-list   (create)
  GET    /{id}/        → project-detail
  PUT    /{id}/        → project-detail (full update)
  PATCH  /{id}/        → project-detail (partial update)
  DELETE /{id}/        → project-detail (destroy)
"""

from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet

router = DefaultRouter()
# Register with empty prefix — the mount point in config/urls.py
# already provides the "projects/" segment.
router.register(r"", ProjectViewSet, basename="project")

urlpatterns = router.urls
