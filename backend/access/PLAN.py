# =============================================================================
# APP: access
# Purpose: RBAC — user-to-OrgUnit assignment and role management
# =============================================================================
#
# ─────────────────────────────────────────────────────────────
# MODELS (access/models.py)
# ─────────────────────────────────────────────────────────────
#
#   RoleChoices (TextChoices enum)
#   ├── ADMIN        = 'admin'
#   ├── HO_USER      = 'ho_user'
#   ├── RO_USER      = 'ro_user'
#   ├── PIU_USER     = 'piu_user'
#   └── PROJECT_USER = 'project_user'
#
#
#   UserOrgAccess (BaseModel)
#   ├── user          FK → accounts.User
#   ├── org_unit      FK → orgs.OrgUnit
#   ├── role          CharField (RoleChoices)
#   └── assigned_by   FK → accounts.User (who created this assignment)
#
#   UNIQUE TOGETHER: (user, org_unit)
#   ↑ One role per user per unit. To have multiple roles in same org,
#     user must be assigned to different units.
#
# ─────────────────────────────────────────────────────────────
# SERVICES (access/services/)
# ─────────────────────────────────────────────────────────────
#
#   access_service.py
#   ├── get_user_org_units(user) → QuerySet[OrgUnit]
#   │     Returns direct OrgUnits assigned to the user
#   │
#   ├── get_user_accessible_units(user) → list[UUID]
#   │     1. Get direct units via get_user_org_units()
#   │     2. For each unit, call hierarchy_service.get_descendants()
#   │     3. Return flat list of all accessible unit IDs
#   │     → This is THE core filtering function
#   │
#   ├── user_has_access_to_unit(user, org_unit_id) → bool
#   │     Quick check if user can access a specific unit
#   │
#   └── user_is_admin(user) → bool
#         True if user has ANY UserOrgAccess with role=ADMIN
#
#   permission_service.py
#   ├── can_create_org_unit(user, org_id) → bool
#   ├── can_edit_road(user, road_id) → bool
#   └── can_manage_users(user) → bool
#
# ─────────────────────────────────────────────────────────────
# DRF PERMISSION CLASSES (access/permissions.py)
# ─────────────────────────────────────────────────────────────
#
#   IsAdminRole
#   └── has_permission: user_is_admin(request.user)
#
#   HasOrgAccess
#   └── has_object_permission: user_has_access_to_unit(user, obj.org_unit_id)
#
#   IsAdminOrReadOnly
#   └── SAFE_METHODS allowed for all, write requires Admin
#
#   These permission classes are COMPOSABLE:
#   permission_classes = [IsAuthenticated, IsAdminRole]
#
# ─────────────────────────────────────────────────────────────
# API VIEWS (access/views.py)
# ─────────────────────────────────────────────────────────────
#
#   UserOrgAccessViewSet  → CRUD  /api/v1/user-access/
#   MyAccessView          → GET   /api/v1/user-access/my/
#     ↑ Returns current user's assigned units + roles
#
# ─────────────────────────────────────────────────────────────
# DASHBOARD VIEWS (access/dashboard_views.py)
# ─────────────────────────────────────────────────────────────
#
#   UserAccessListPage    → /dashboard/user-access/
#   AssignAccessPage      → /dashboard/user-access/assign/
#   UserAccessDetailPage  → /dashboard/user-access/<user_id>/
# =============================================================================
