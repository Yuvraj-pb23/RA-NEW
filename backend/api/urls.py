"""
api/urls.py
===========
URL namespace for the entire API surface.

Included by:  config/urls.py  →  path('api/', include('api.urls'))

URL layout
----------
  /api/v1/                          All DRF router endpoints (CRUD + actions)
  /api/v1/auth/token/               Obtain JWT token pair (POST)
  /api/v1/auth/token/refresh/       Refresh access token   (POST)
  /api/v1/auth/token/verify/        Verify a token         (POST)
  /api/schema/                      OpenAPI YAML schema    (GET)
  /api/docs/                        Swagger UI             (GET)
  /api/redoc/                       ReDoc UI               (GET)
"""
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from api.v1.router import router
from api.v1.views import dashboard_stats
from api.views import DashboardStatsAPIView

app_name = "api"

# ── JWT auth endpoints ─────────────────────────────────────────────────────
auth_patterns = [
    path("token/",         TokenObtainPairView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(),   name="token-refresh"),
    path("token/verify/",  TokenVerifyView.as_view(),    name="token-verify"),
]

# ── Schema / docs ──────────────────────────────────────────────────────────
schema_patterns = [
    path("schema/", SpectacularAPIView.as_view(),                   name="schema"),
    path("docs/",   SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger-ui"),
    path("redoc/",  SpectacularRedocView.as_view(url_name="api:schema"),   name="redoc"),
]

urlpatterns = [
    # All CRUD + custom actions
    path("v1/",      include(router.urls)),
    path("v1/auth/", include(auth_patterns)),
    path("v1/dashboard/", dashboard_stats, name="dashboard-stats-v1"),
    path("dashboard/", DashboardStatsAPIView.as_view(), name="dashboard-stats"),

    # Developer documentation (schema lives at /api/ level for easy discoverability)
    *schema_patterns,
]
