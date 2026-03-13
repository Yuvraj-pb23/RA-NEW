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

from .models import Road
from .serializers import RoadSerializer


# ── FilterSet ─────────────────────────────────────────────────────────────────

class RoadFilter(django_filters.FilterSet):
    project      = django_filters.UUIDFilter(field_name="project__id")
    organization = django_filters.UUIDFilter(field_name="project__organization__id")
    road_type    = django_filters.CharFilter(field_name="road_type")
    name         = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model  = Road
        fields = ["project", "organization", "road_type", "name"]


# ── ViewSet ───────────────────────────────────────────────────────────────────

class RoadViewSet(ModelViewSet):
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
