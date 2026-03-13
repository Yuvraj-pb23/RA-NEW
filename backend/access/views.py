"""
access/views.py
===============
ViewSet for UserOrgAccess.

Endpoints:
  GET    /api/user-access/          -> list all access records
  POST   /api/user-access/          -> assign user to org unit
  GET    /api/user-access/{id}/     -> retrieve one record
  DELETE /api/user-access/{id}/     -> remove access

Extra read actions:
  GET    /api/user-access/by-org-unit/?org_unit=<uuid>
         -> list all users assigned to a specific org unit

  GET    /api/user-access/my/
         -> list the requesting user's own access records

Filter params:
  ?user=<uuid>
  ?org_unit=<uuid>
  ?role=admin|ho|ro|piu|project
  ?organization=<uuid>        (filters via org_unit__organization)
  ?is_active=true|false
"""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import UserOrgAccess
from .serializers import UserOrgAccessSerializer


# ── FilterSet ─────────────────────────────────────────────────────────────────

class UserOrgAccessFilter(django_filters.FilterSet):
    user         = django_filters.UUIDFilter(field_name="user__id")
    org_unit     = django_filters.UUIDFilter(field_name="org_unit__id")
    organization = django_filters.UUIDFilter(field_name="org_unit__organization__id")
    role         = django_filters.CharFilter(field_name="role")
    is_active    = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model  = UserOrgAccess
        fields = ["user", "org_unit", "organization", "role", "is_active"]


# ── ViewSet ───────────────────────────────────────────────────────────────────

class UserOrgAccessViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """
    POST   /api/user-access/       -> assign user to org unit
    GET    /api/user-access/       -> list access records
    GET    /api/user-access/{id}/  -> retrieve one record
    DELETE /api/user-access/{id}/  -> remove access
    """

    queryset = (
        UserOrgAccess.objects
        .select_related(
            "user",
            "org_unit",
            "org_unit__level",
            "org_unit__organization",
            "assigned_by",
        )
        .order_by("-created_at")
    )
    serializer_class = UserOrgAccessSerializer
    permission_classes = [IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class  = UserOrgAccessFilter
    search_fields    = ["user__email", "org_unit__name"]
    ordering_fields  = ["created_at", "role"]
    ordering         = ["-created_at"]

    # ── Extra read actions ─────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="by-org-unit")
    def by_org_unit(self, request):
        """
        GET /api/user-access/by-org-unit/?org_unit=<uuid>
        Lists all users assigned to a specific org unit.
        """
        org_unit_id = request.query_params.get("org_unit")
        if not org_unit_id:
            return Response(
                {"detail": "?org_unit=<uuid> is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(org_unit_id=org_unit_id)
        qs = self.filter_queryset(qs)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="my")
    def my(self, request):
        """
        GET /api/user-access/my/
        Returns the requesting user's own active access records.
        """
        qs = (
            UserOrgAccess.objects
            .filter(user=request.user, is_active=True)
            .select_related(
                "user",
                "org_unit",
                "org_unit__level",
                "org_unit__organization",
                "assigned_by",
            )
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
