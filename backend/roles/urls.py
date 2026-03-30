"""
roles/urls.py
=============
App-level URL file for the roles app.
Primary routing is handled via api/urls.py router.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from roles.views import RoleViewSet

router = DefaultRouter()
router.register(r"roles", RoleViewSet, basename="role")

app_name = "roles"

urlpatterns = [
    path("", include(router.urls)),
]
