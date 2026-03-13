# =============================================================================
# APP: roads
# Purpose: Projects and Roads — the domain data
# =============================================================================
#
# ─────────────────────────────────────────────────────────────
# MODELS (roads/models.py)
# ─────────────────────────────────────────────────────────────
#
#   Project (BaseModel)
#   ├── name          CharField
#   ├── org_unit      FK → orgs.OrgUnit
#   │     The unit this project BELONGS to (e.g., PIU Agra)
#   │     Determines who can see/manage this project
#   ├── description   TextField (optional)
#   ├── start_date    DateField (optional)
#   └── end_date      DateField (optional)
#
#
#   Road (BaseModel)
#   ├── name          CharField
#   ├── project       FK → Project
#   ├── length_km     DecimalField(10, 3)
#   ├── road_type     CharField  (National Highway, State Highway, etc.)
#   ├── geometry      JSONField  (GeoJSON LineString — Phase 1)
#   │     Phase 2: replace with PostGIS GeometryField(LineString, srid=4326)
#   └── metadata      JSONField  (additional road attributes)
#
#   INDEX: project (for road listing performance)
#
# ─────────────────────────────────────────────────────────────
# SERVICES (roads/services/)
# ─────────────────────────────────────────────────────────────
#
#   road_service.py
#   ├── get_roads_for_user(user) → QuerySet[Road]
#   │     1. access_service.get_user_accessible_units(user) → unit_ids
#   │     2. Project.objects.filter(org_unit__in=unit_ids) → project_ids
#   │     3. Road.objects.filter(project__in=project_ids)
#   │     → This is THE road filtering pipeline
#   │
#   ├── get_roads_for_project(project_id, user) → QuerySet[Road]
#   │     Checks user has access to the project's org_unit first
#   │
#   └── get_roads_for_org(org_id, user) → QuerySet[Road]
#         All roads within an organization (admin only)
#
# ─────────────────────────────────────────────────────────────
# API VIEWS (roads/views.py)
# ─────────────────────────────────────────────────────────────
#
#   ProjectViewSet   → CRUD   /api/v1/projects/
#   RoadViewSet      → CRUD   /api/v1/roads/
#
#   Filtering on RoadViewSet:
#     ?project=<id>      → roads for specific project
#     ?org_unit=<id>     → roads for org unit (recursive)
#     ?org=<id>          → roads for entire org (admin)
#
#   ALL LIST endpoints apply get_roads_for_user() automatically
#   via a custom QuerySet mixin.
#
# ─────────────────────────────────────────────────────────────
# SERIALIZERS (roads/serializers.py)
# ─────────────────────────────────────────────────────────────
#
#   ProjectSerializer        (includes org_unit nested)
#   ProjectCreateSerializer  (accepts org_unit_id)
#   RoadSerializer           (includes project nested)
#   RoadCreateSerializer     (accepts project_id, geometry as GeoJSON dict)
#   RoadGeoJSONSerializer    (for map endpoints — returns FeatureCollection)
#
# ─────────────────────────────────────────────────────────────
# DASHBOARD VIEWS (roads/dashboard_views.py)
# ─────────────────────────────────────────────────────────────
#
#   ProjectListPage    → /dashboard/projects/
#   ProjectCreatePage  → /dashboard/projects/create/
#   RoadListPage       → /dashboard/roads/
#   RoadCreatePage     → /dashboard/roads/create/
#   RoadDetailPage     → /dashboard/roads/<id>/      (with geometry preview)
# =============================================================================
