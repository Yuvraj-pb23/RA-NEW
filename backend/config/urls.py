"""
config/urls.py — root URL configuration
=========================================
Mounts top-level URL namespaces:

  /admin/      → Django built-in admin  (superuser only)
  /api/        → DRF REST API  (JWT auth, see api/urls.py)
  /dashboard/  → HTML admin dashboard   (session auth)

Auth for the dashboard HTML login/logout is handled inside
dashboard/urls.py so this file stays clean.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # ── Django admin ──────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Projects API  ─────────────────────────────────────────────────────
    # Mounted at /api/projects/ (flat, no v1 prefix).
    path("api/projects/", include("projects.urls")),
    # ── Roads API  ───────────────────────────────────────────────────────
    # Mounted at /api/roads/ (flat, no v1 prefix).
    path("api/roads/", include("roads.urls")),
    # ── User Access API  ───────────────────────────────────────────────
    # Mounted at /api/user-access/ (flat, no v1 prefix).
    path("api/user-access/", include("access.urls")),    # ── REST API  ─────────────────────────────────────────────────────────
    # All routes are under /api/ — see api/urls.py for the sub-routing.
    path("api/", include("api.urls", namespace="api")),

    # ── HTML dashboard  ───────────────────────────────────────────────────
    # Template-rendered views; uses Django sessions.
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
]
