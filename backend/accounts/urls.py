"""
accounts/urls.py
================
App-level URL file for the accounts app.

In the current routing setup these routes are served via the DRF
router registered in api/v1/router.py.  This file is provided so
that the app is self-contained and can be included independently if
needed (e.g. in tests).

All endpoints are under the prefix the router assigns:
  /api/v1/users/
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

app_name = "accounts"

urlpatterns = [
    path("", include(router.urls)),
]
