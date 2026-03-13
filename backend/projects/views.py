"""
projects/views.py
=================
DRF ViewSet for the Project resource.

ProjectFilter
  - organization : filter by organization UUID
  - org_unit     : filter by org_unit UUID
  - name         : case-insensitive substring filter

ProjectViewSet
  - Full CRUD (ModelViewSet)
  - Filter  : DjangoFilterBackend  (organization, org_unit, name)
  - Search  : SearchFilter          (name, description)
  - Order   : OrderingFilter        (name, created_at)
  - select_related includes org_unit__level so validation/serializer
    reads org_unit.level.level_name without extra DB hits.
"""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from .models import Project
from .serializers import ProjectSerializer


# ── FilterSet ─────────────────────────────────────────────────────────────────

class ProjectFilter(django_filters.FilterSet):
    organization = django_filters.UUIDFilter(field_name="organization__id")
    org_unit     = django_filters.UUIDFilter(field_name="org_unit__id")
    name         = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model  = Project
        fields = ["organization", "org_unit", "name"]


# ── ViewSet ───────────────────────────────────────────────────────────────────

class ProjectViewSet(ModelViewSet):
    """
    list:   GET  /api/projects/
    create: POST /api/projects/
    retrieve: GET  /api/projects/{id}/
    update:   PUT  /api/projects/{id}/
    partial_update: PATCH /api/projects/{id}/
    destroy: DELETE /api/projects/{id}/
    """

    queryset = (
        Project.objects
        .select_related(
            "organization",
            "org_unit",
            "org_unit__level",          # needed for Rule 1 validation
            "org_unit__organization",    # needed for Rule 2 validation
        )
        .all()
    )
    serializer_class  = ProjectSerializer
    filter_backends   = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class   = ProjectFilter
    search_fields     = ["name", "description"]
    ordering_fields   = ["name", "created_at"]
    ordering          = ["-created_at"]
