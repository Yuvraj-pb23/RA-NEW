"""
roads/views.py
==============
DRF ViewSet for the Road resource.

RoadFilter
  - project      : filter by project UUID
  - organization : filter by organization UUID
  - road_type    : filter by road type code (NH, SH, MDR, ODR, VR)
  - name         : case-insensitive substring filter

RoadViewSet
  - Full CRUD (ModelViewSet)
  - Filter  : DjangoFilterBackend  (project, organization, road_type, name)
  - Search  : SearchFilter          (name, project__name)
  - Order   : OrderingFilter        (name, length, created_at)
  - Optimized queryset with select_related across 2 levels.
"""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from access.permissions import IsAdminOrReadOnly
from django.http import JsonResponse
from django.db.models import Q
from .utils import parse_gpx

from .models import Road
from .serializers import RoadSerializer


# ── FilterSet ─────────────────────────────────────────────────────────────────

class RoadFilter(django_filters.FilterSet):
    project      = django_filters.UUIDFilter(field_name="project__id")
    organization = django_filters.UUIDFilter(field_name="project__organization__id")
    ho_user      = django_filters.Filter(method="filter_ho_user")
    ro_user      = django_filters.Filter(method="filter_ro_user")
    piu_user     = django_filters.Filter(method="filter_piu_user")
    project_user = django_filters.UUIDFilter(field_name="project__project_user__id")
    road_type    = django_filters.CharFilter(field_name="road_type")
    name         = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model  = Road
        fields = ["project", "organization", "ho_user", "ro_user", "piu_user", "project_user", "road_type", "name"]

    def filter_ho_user(self, queryset, name, value):
        from accounts.models import User
        from access.utils import get_user_accessible_units
        try:
            target_user = User.objects.get(id=value)
            accessible_units = get_user_accessible_units(target_user)
            return queryset.filter(
                Q(project__ho_user__id=value) |
                Q(project__ro_user__ho_user__id=value) |
                Q(project__piu_user__ho_user__id=value) |
                Q(project__project_user__ho_user__id=value) |
                Q(project__org_unit__in=accessible_units)
            ).distinct()
        except User.DoesNotExist:
            return queryset.none()

    def filter_ro_user(self, queryset, name, value):
        from accounts.models import User
        from access.utils import get_user_accessible_units
        try:
            target_user = User.objects.get(id=value)
            accessible_units = get_user_accessible_units(target_user)
            return queryset.filter(
                Q(project__ro_user__id=value) |
                Q(project__piu_user__ro_user__id=value) |
                Q(project__project_user__ro_user__id=value) |
                Q(project__org_unit__in=accessible_units)
            ).distinct()
        except User.DoesNotExist:
            return queryset.none()

    def filter_piu_user(self, queryset, name, value):
        from accounts.models import User
        from access.utils import get_user_accessible_units
        try:
            target_user = User.objects.get(id=value)
            accessible_units = get_user_accessible_units(target_user)
            return queryset.filter(
                Q(project__piu_user__id=value) |
                Q(project__project_user__piu_user__id=value) |
                Q(project__org_unit__in=accessible_units)
            ).distinct()
        except User.DoesNotExist:
            return queryset.none()


# ── ViewSet ───────────────────────────────────────────────────────────────────

class RoadViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    """
    list:           GET    /api/roads/
    create:         POST   /api/roads/
    retrieve:       GET    /api/roads/{id}/
    update:         PUT    /api/roads/{id}/
    partial_update: PATCH  /api/roads/{id}/
    destroy:        DELETE /api/roads/{id}/
    """

    queryset = (
        Road.objects
        .select_related(
            "project",                  # Road → Project
            "project__organization",    # Project → Organization (for display + filter)
        )
        .all()
    )
    serializer_class = RoadSerializer
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class  = RoadFilter
    search_fields    = ["name", "project__name"]
    ordering_fields  = ["name", "length", "created_at"]
    ordering         = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        from accounts.models import SystemRole
        from access.utils import get_user_accessible_units
        from django.db.models import Q
        
        user = self.request.user
        role = getattr(user, 'role', None)
        
        if role == SystemRole.SUPER_ADMIN:
            return qs
            
        if role in [SystemRole.ORG_ADMIN, SystemRole.HO_USER]:
            if user.organization:
                return qs.filter(project__organization=user.organization)
            return qs.none()
            
        accessible_units = get_user_accessible_units(user)
        visibility_q = Q(project__org_unit__in=accessible_units)
        
        if role == SystemRole.RO_USER:
            visibility_q |= Q(project__ro_user=user)
        elif role == SystemRole.PIU_USER:
            visibility_q |= Q(project__piu_user=user)
        elif role == SystemRole.PROJECT_USER:
            visibility_q |= Q(project__project_user=user)
            
        return qs.filter(visibility_q).distinct()

from django.contrib.auth.decorators import login_required

@login_required
def road_gpx_view(request, road_id):
    try:
        from accounts.models import SystemRole
        from access.utils import get_user_accessible_units
        
        qs = Road.objects.all()
        if request.user.role != SystemRole.SUPER_ADMIN:
            if request.user.organization:
                qs = qs.filter(project__organization=request.user.organization)
            else:
                qs = qs.none()
            
        road = qs.get(id=road_id)
        if road.gpx_file:
            data = parse_gpx(road.gpx_file.path)
            return JsonResponse(data)
        return JsonResponse({"error": "No GPX file found"}, status=404)
    except Road.DoesNotExist:
        return JsonResponse({"error": "Road not found"}, status=404)
