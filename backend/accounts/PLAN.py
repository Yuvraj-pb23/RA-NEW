# =============================================================================
# APP: accounts
# Purpose: Custom User model, authentication, profile
# =============================================================================
#
# MODELS (accounts/models.py):
#
#   User (extends AbstractUser)
#   ├── id           → UUID (from core.BaseModel)
#   ├── email        → unique, used as login identifier
#   ├── full_name    → CharField
#   ├── phone        → CharField (optional)
#   ├── is_active    → BooleanField
#   └── created_at   → auto
#
#   Note: username = email (set USERNAME_FIELD = 'email')
#   AUTH_USER_MODEL = 'accounts.User' in settings
#
# VIEWS (accounts/views.py):
#
#   LoginView        → POST /api/v1/auth/login/   (returns JWT tokens)
#   LogoutView       → POST /api/v1/auth/logout/  (blacklist refresh token)
#   MeView           → GET  /api/v1/auth/me/      (current user profile)
#   UserListView     → GET  /api/v1/users/         (admin only)
#   UserDetailView   → GET/PATCH /api/v1/users/<id>/
#
# SERIALIZERS (accounts/serializers.py):
#
#   UserSerializer          → read-only profile data
#   UserCreateSerializer    → create user with password hashing
#   UserUpdateSerializer    → partial update (no password here)
#
# DASHBOARD VIEWS (accounts/dashboard_views.py):
#   UserListPage     → /dashboard/users/           (HTML)
#   UserDetailPage   → /dashboard/users/<id>/      (HTML)
#
# TESTS (accounts/tests/):
#   test_models.py
#   test_views.py
#   test_auth.py
# =============================================================================
