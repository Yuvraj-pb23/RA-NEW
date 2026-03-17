from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from access.permissions import IsAdminOrReadOnly
from core.permissions import IsOrgAdminOrReadOnly, IsSuperAdminOrReadOnly, IsSuperAdminOrReadOnly
from .models import Organization, HierarchyLevel, OrgUnit
from .serializers import (
    OrganizationSerializer,
    HierarchyLevelSerializer,
    OrgUnitSerializer,
    OrgUnitTreeSerializer,
)


# =============================================================================
# Organization ViewSet
# =============================================================================

class OrganizationViewSet(viewsets.ModelViewSet):
    """
    CRUD for organizations.

    list     GET    /api/v1/organizations/
    create   POST   /api/v1/organizations/
    retrieve GET    /api/v1/organizations/<id>/
    update   PUT    /api/v1/organizations/<id>/
    partial  PATCH  /api/v1/organizations/<id>/
    destroy  DELETE /api/v1/organizations/<id>/

    Extra action:
    stats    GET    /api/v1/organizations/<id>/stats/
    """

    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["country", "is_active"]
    search_fields    = ["name", "country"]
    ordering_fields  = ["name", "country", "created_at"]
    ordering         = ["name"]

    def get_permissions(self):
        from accounts.models import SystemRole
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            from core.permissions import IsSuperAdmin
            return [IsAuthenticated(), IsSuperAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Annotate each org with unit_count and project_count
        to avoid N+1 in the list view.
        """
        qs = Organization.objects.annotate(
            unit_count=Count("org_units", distinct=True),
            project_count=Count("org_units__org_unit_projects", distinct=True),
            road_count=Count("org_units__org_unit_projects__roads", distinct=True),
        )
        from accounts.models import SystemRole
        user = self.request.user
        if user.role == SystemRole.SUPER_ADMIN:
            return qs
        return qs.filter(id=user.organization_id)

    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        """
        GET /api/v1/organizations/<id>/stats/
        Returns summary stats for a single organization.
        """
        org = self.get_object()
        from roads.models import Road  # noqa: PLC0415
        from projects.models import Project as OrgProject  # noqa: PLC0415
        road_qs = Road.objects.filter(project__organization=org)

        data = {
            "organization_id":   str(org.id),
            "organization_name": org.name,
            "total_units":       org.org_units.filter(is_active=True).count(),
            "total_projects":    OrgProject.objects.filter(organization=org).count(),
            "total_roads":       road_qs.count(),
            "total_length_km":   road_qs.aggregate(
                total=__import__("django.db.models", fromlist=["Sum"]).Sum("length")
            )["total"] or 0,
        }
        return Response(data)


# =============================================================================
# HierarchyLevel ViewSet
# =============================================================================

class HierarchyLevelViewSet(viewsets.ModelViewSet):
    """
    CRUD for hierarchy level definitions.

    list     GET    /api/v1/hierarchy-levels/
    create   POST   /api/v1/hierarchy-levels/
    retrieve GET    /api/v1/hierarchy-levels/<id>/
    update   PUT    /api/v1/hierarchy-levels/<id>/
    partial  PATCH  /api/v1/hierarchy-levels/<id>/
    destroy  DELETE /api/v1/hierarchy-levels/<id>/

    Filter by org:  ?organization=<uuid>
    """

    queryset = HierarchyLevel.objects.select_related("organization", "parent_level")
    serializer_class = HierarchyLevelSerializer
    permission_classes = [IsAuthenticated, IsOrgAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["organization"]
    ordering_fields  = ["level_order", "level_name"]
    ordering         = ["organization", "level_order"]

    def get_queryset(self):
        qs = super().get_queryset()
        from accounts.models import SystemRole
        user = self.request.user
        if user.role == SystemRole.SUPER_ADMIN:
            return qs
        return qs.filter(organization=user.organization)

    def destroy(self, request, *args, **kwargs):
        """
        Prevent deletion if any OrgUnits use this level.
        The model already has on_delete=PROTECT, but this gives a
        cleaner API error message.
        """
        instance = self.get_object()
        if instance.org_units.exists():
            return Response(
                {
                    "error": True,
                    "message": (
                        f"Cannot delete level '{instance.level_name}' — "
                        f"{instance.org_units.count()} org unit(s) are using it."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)


# =============================================================================
# OrgUnit ViewSet
# =============================================================================

class OrgUnitViewSet(viewsets.ModelViewSet):
    """
    CRUD for org units.

    list     GET    /api/v1/org-units/
    create   POST   /api/v1/org-units/
    retrieve GET    /api/v1/org-units/<id>/
    update   PUT    /api/v1/org-units/<id>/
    partial  PATCH  /api/v1/org-units/<id>/
    destroy  DELETE /api/v1/org-units/<id>/

    Extra actions:
    tree        GET  /api/v1/org-units/tree/?organization=<uuid>
    children    GET  /api/v1/org-units/<id>/children/
    ancestors   GET  /api/v1/org-units/<id>/ancestors/
    """

    queryset = OrgUnit.objects.select_related(
        "organization", "level", "parent_unit", "parent_unit__level"
    )
    serializer_class = OrgUnitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["organization", "level", "parent_unit", "is_active"]
    search_fields    = ["name"]
    ordering_fields  = ["name", "level__level_order", "created_at"]
    ordering         = ["level__level_order", "name"]

    def get_queryset(self):
        qs = super().get_queryset()
        from accounts.models import SystemRole
        if self.request.user.role == SystemRole.SUPER_ADMIN:
            return qs
        from access.utils import get_user_accessible_units
        accessible_units = get_user_accessible_units(self.request.user)
        return qs.filter(id__in=accessible_units)

    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request):
        """
        GET /api/v1/org-units/tree/?organization=<uuid>

        Returns the full hierarchy as a nested tree JSON.

        Algorithm (O(n), single DB query):
        1. Fetch all OrgUnits for the org in one query, ordered by level_order.
        2. Build a dict: {id → unit}.
        3. Walk the list, attaching children to their parent's _children_cache.
        4. Serialize only root nodes (parent_unit=None) — children are nested.
        """
        org_id = request.query_params.get("organization")
        if not org_id:
            return Response(
                {"error": True, "message": "?organization=<uuid> is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        units = list(
            OrgUnit.objects
            .filter(organization_id=org_id, is_active=True)
            .select_related("level")
            .order_by("level__level_order", "name")
        )

        # Initialise children cache on each instance
        unit_map = {str(u.id): u for u in units}
        for u in units:
            u._children_cache = []

        roots = []
        for u in units:
            if u.parent_unit_id is None:
                roots.append(u)
            else:
                parent = unit_map.get(str(u.parent_unit_id))
                if parent is not None:
                    parent._children_cache.append(u)

        serializer = OrgUnitTreeSerializer(roots, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="children")
    def children(self, request, pk=None):
        """
        GET /api/v1/org-units/<id>/children/
        Returns DIRECT children only (not recursive).
        """
        unit = self.get_object()
        children = unit.children.filter(is_active=True).select_related("level")
        serializer = OrgUnitSerializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="ancestors")
    def ancestors(self, request, pk=None):
        """
        GET /api/v1/org-units/<id>/ancestors/
        Returns path from root to parent of this unit (ordered root-first).
        """
        unit = self.get_object()
        ancestors = unit.get_ancestors()  # defined on the model
        serializer = OrgUnitSerializer(ancestors, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Prevent deletion if unit has projects — give a clear error.
        Cascading child OrgUnit deletion is handled by the DB (on_delete=CASCADE).
        """
        instance = self.get_object()
        project_count = instance.projects.count()
        if project_count:
            return Response(
                {
                    "error": True,
                    "message": (
                        f"Cannot delete '{instance.name}' — "
                        f"{project_count} project(s) are assigned to it."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)
