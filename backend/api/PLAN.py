# =============================================================================
# APP: api
# Purpose: Central DRF router, versioning, OpenAPI schema config
# =============================================================================
#
# STRUCTURE:
#
#   api/
#   ├── v1/
#   │   ├── __init__.py
#   │   └── router.py      ← all ViewSets registered here
#   │
#   ├── urls.py            ← include v1 router + auth token URLs
#   └── schema.py          ← drf-spectacular settings
#
# ROUTER REGISTRATION (api/v1/router.py):
#
#   router = DefaultRouter()
#   router.register('organizations',   OrganizationViewSet)
#   router.register('hierarchy-levels', HierarchyLevelViewSet)
#   router.register('org-units',       OrgUnitViewSet)
#   router.register('projects',        ProjectViewSet)
#   router.register('roads',           RoadViewSet)
#   router.register('users',           UserViewSet)
#   router.register('user-access',     UserOrgAccessViewSet)
#
# URL PATTERNS (api/urls.py):
#
#   /api/v1/              → v1 router
#   /api/v1/auth/token/   → JWT obtain pair
#   /api/v1/auth/refresh/ → JWT refresh
#   /api/v1/auth/me/      → current user
#   /api/schema/          → OpenAPI YAML
#   /api/docs/            → Swagger UI
#
# VERSIONING NOTE:
#   URL-based versioning chosen (/api/v1/, /api/v2/)
#   Keep v1 stable; new breaking changes go into v2.
#
# AUTHENTICATION ON API:
#   DEFAULT_AUTHENTICATION_CLASSES = [
#       JWTAuthentication,
#       SessionAuthentication,   ← allows browsable API with session
#   ]
#   DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]
# =============================================================================
