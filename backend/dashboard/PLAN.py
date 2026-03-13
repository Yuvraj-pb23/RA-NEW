# =============================================================================
# APP: dashboard
# Purpose: Server-rendered HTML pages for the Admin UI
# This app renders templates only — NO business logic here.
# Business logic lives in services/. API calls come from the templates via JS.
# =============================================================================
#
# DESIGN PATTERN:
#
#   Dashboard views are thin wrappers:
#   1. Check user is authenticated (session)
#   2. Pass minimal context to template (user info, page title)
#   3. Template renders the Tailwind UI
#   4. All dynamic data loaded via fetch() → /api/v1/ endpoints
#
#   This makes the dashboard a "single-page app lite" without a full SPA.
#
# ─────────────────────────────────────────────────────────────
# VIEWS (dashboard/views.py)
# ─────────────────────────────────────────────────────────────
#
#   DashboardHomeView          → /dashboard/
#   OrganizationListView       → /dashboard/organizations/
#   OrganizationCreateView     → /dashboard/organizations/create/
#   HierarchyBuilderView       → /dashboard/hierarchy/<org_id>/
#   OrgUnitListView            → /dashboard/org-units/
#   ProjectListView            → /dashboard/projects/
#   RoadListView               → /dashboard/roads/
#   UserListView               → /dashboard/users/
#   UserAccessView             → /dashboard/user-access/
#   ReportsView                → /dashboard/reports/
#   SettingsView               → /dashboard/settings/
#
# ─────────────────────────────────────────────────────────────
# TEMPLATE STRUCTURE (templates/)
# ─────────────────────────────────────────────────────────────
#
#   layouts/
#   └── base.html               ← base layout with sidebar + topbar
#
#   components/
#   ├── sidebar.html            ← navigation sidebar
#   ├── topbar.html             ← header with user menu
#   ├── stats_card.html         ← reusable stats widget
#   ├── table.html              ← reusable data table
#   ├── modal.html              ← reusable modal
#   ├── breadcrumb.html         ← hierarchy breadcrumb
#   └── tree_node.html          ← recursive tree node for hierarchy viewer
#
#   dashboard/
#   ├── home.html               ← overview with stats
#   ├── organizations/
#   │   ├── list.html
#   │   └── form.html
#   ├── hierarchy/
#   │   ├── builder.html        ← drag/configure levels
#   │   └── tree.html           ← read-only tree view
#   ├── org_units/
#   │   ├── list.html
#   │   └── form.html
#   ├── projects/
#   │   ├── list.html
#   │   └── form.html
#   ├── roads/
#   │   ├── list.html
#   │   ├── form.html
#   │   └── detail.html
#   ├── users/
#   │   ├── list.html
#   │   └── detail.html
#   └── user_access/
#       ├── list.html
#       └── assign.html
#
# ─────────────────────────────────────────────────────────────
# FRONTEND ASSETS
# ─────────────────────────────────────────────────────────────
#
#   static/css/main.css        ← Tailwind compiled output
#   static/js/app.js           ← Alpine.js initialization
#   static/js/api.js           ← fetch() wrapper for /api/v1/
#   static/js/tree.js          ← hierarchy tree rendering
#
# ─────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION ITEMS
# ─────────────────────────────────────────────────────────────
#
#   Dashboard          /dashboard/
#   Organizations      /dashboard/organizations/
#   Hierarchy          /dashboard/hierarchy/
#   Org Units          /dashboard/org-units/
#   Projects           /dashboard/projects/
#   Roads              /dashboard/roads/
#   Users              /dashboard/users/
#   User Access        /dashboard/user-access/
#   Reports            /dashboard/reports/
#   Settings           /dashboard/settings/
# =============================================================================
