# =============================================================================
# APP: orgs
# Purpose: Organization, HierarchyLevel, OrgUnit (the dynamic tree)
# This is the CORE structural app.
# =============================================================================
#
# ─────────────────────────────────────────────────────────────
# MODELS (orgs/models.py)
# ─────────────────────────────────────────────────────────────
#
#   Organization (BaseModel)
#   ├── name         CharField unique
#   ├── country      CharField
#   └── description  TextField (optional)
#
#
#   HierarchyLevel (BaseModel)
#   ├── organization  FK → Organization
#   ├── level_name    CharField  e.g. "HO", "RO", "PIU"
#   ├── level_order   PositiveIntegerField  (1=top)
#   └── parent_level  FK → self (nullable)  ← sibling levels share same parent
#
#   UNIQUE TOGETHER: (organization, level_order)
#   UNIQUE TOGETHER: (organization, level_name)
#
#   Purpose: This is the TEMPLATE/SCHEMA for an org's hierarchy.
#   It does NOT hold actual units — just the level definitions.
#
#
#   OrgUnit (BaseModel)
#   ├── organization   FK → Organization
#   ├── name           CharField
#   ├── level          FK → HierarchyLevel
#   ├── parent_unit    FK → self (nullable)  ← TREE relationship
#   └── metadata       JSONField (optional — for extra attributes)
#
#   UNIQUE TOGETHER: (organization, name)
#   INDEX: parent_unit (for CTE traversal performance)
#
#   This is the ACTUAL TREE of units:
#   HO Delhi → RO Lucknow → PIU Agra → Project NH-24
#
# ─────────────────────────────────────────────────────────────
# SERVICES (orgs/services/)
# ─────────────────────────────────────────────────────────────
#
#   hierarchy_service.py
#   ├── get_descendants(org_unit_id) → list[OrgUnit]
#   │     Uses PostgreSQL recursive CTE
#   │     Returns flat list of all child units at any depth
#   │
#   ├── get_ancestors(org_unit_id) → list[OrgUnit]
#   │     Walks UP the tree from given unit
#   │
#   ├── build_tree(org_id) → nested dict
#   │     Converts flat OrgUnit list → nested JSON tree
#   │     Used by the Hierarchy Tree Viewer page
#   │
#   └── validate_hierarchy(level_id, parent_unit_id) → bool
#         Ensures parent's level is exactly one level above child's level
#         Prevents assigning a PIU as parent of an HO
#
# ─────────────────────────────────────────────────────────────
# API VIEWS (orgs/views.py)
# ─────────────────────────────────────────────────────────────
#
#   OrganizationViewSet    → CRUD  /api/v1/organizations/
#   HierarchyLevelViewSet  → CRUD  /api/v1/hierarchy-levels/
#   OrgUnitViewSet         → CRUD  /api/v1/org-units/
#   HierarchyTreeView      → GET   /api/v1/org-units/tree/?org=<id>
#     ↑ calls hierarchy_service.build_tree() and returns nested JSON
#
# ─────────────────────────────────────────────────────────────
# SERIALIZERS (orgs/serializers.py)
# ─────────────────────────────────────────────────────────────
#
#   OrganizationSerializer
#   HierarchyLevelSerializer  (includes parent_level detail nested)
#   OrgUnitSerializer         (includes level detail nested)
#   OrgUnitTreeSerializer     (recursive, for tree endpoint)
#
# ─────────────────────────────────────────────────────────────
# DASHBOARD VIEWS (orgs/dashboard_views.py)
# ─────────────────────────────────────────────────────────────
#
#   OrgListPage           → /dashboard/organizations/
#   OrgCreatePage         → /dashboard/organizations/create/
#   HierarchyBuilderPage  → /dashboard/hierarchy/         ← visual tree builder
#   OrgUnitListPage       → /dashboard/org-units/
#   OrgUnitCreatePage     → /dashboard/org-units/create/
#   HierarchyTreePage     → /dashboard/hierarchy/tree/    ← read-only tree view
#
# ─────────────────────────────────────────────────────────────
# PERMISSION LOGIC
# ─────────────────────────────────────────────────────────────
#
#   Only Admin role can CREATE/UPDATE/DELETE organizations and levels.
#   Any authenticated user can READ the hierarchy tree.
#   OrgUnit creation restricted to Admin or HO User of that org.
# =============================================================================
