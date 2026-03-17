"""
config/urls.py — root URL configuration
"""
from django.contrib import admin
from django.urls import include, path
from dashboard.views import LandingView

urlpatterns = [
    # ── Root: beautiful landing page ──────────────────────────────────────
    path("", LandingView.as_view()),

    # ── Django admin ──────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Projects API  ─────────────────────────────────────────────────────
    path("api/projects/", include("projects.urls")),
    # ── Roads API  ───────────────────────────────────────────────────────
    path("api/roads/", include("roads.urls")),
    # ── User Access API  ───────────────────────────────────────────────
    path("api/user-access/", include("access.urls")),
    # ── REST API  ─────────────────────────────────────────────────────────
    path("api/", include("api.urls", namespace="api")),

    # ── HTML dashboard  ───────────────────────────────────────────────────
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
]
