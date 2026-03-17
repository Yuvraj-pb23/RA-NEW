from django.contrib.auth import get_user_model
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from access.permissions import IsAdminRole, IsSelfOrAdmin
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    User management endpoints.

    list     GET    /api/v1/users/                (Admin only)
    create   POST   /api/v1/users/                (Admin only)
    retrieve GET    /api/v1/users/<id>/           (self or Admin)
    update   PUT    /api/v1/users/<id>/           (self or Admin)
    partial  PATCH  /api/v1/users/<id>/           (self or Admin)
    destroy  DELETE /api/v1/users/<id>/           (Admin only)

    Extra actions:
    me            GET   /api/v1/users/me/         (current user's profile)
    set_password  POST  /api/v1/users/<id>/set-password/
    """

    def get_queryset(self):
        qs = User.objects.all().order_by("email")
        user = self.request.user

        if getattr(user, 'role', None) == 'SUPER_ADMIN':
            return qs

        if getattr(user, 'role', None) == 'ORG_ADMIN':
            # Resolve org: prefer the direct FK, fall back to UserOrgAccess
            org = user.organization
            if org is None:
                from access.models import UserOrgAccess
                access = UserOrgAccess.objects.filter(
                    user=user, is_active=True
                ).select_related('org_unit__organization').first()
                if access:
                    org = access.org_unit.organization

            if org is None:
                return qs.none()

            # Show users matched by org FK OR by an active UserOrgAccess
            # within any unit of this org (covers users whose org FK wasn't set)
            from access.models import UserOrgAccess
            user_ids_via_access = UserOrgAccess.objects.filter(
                org_unit__organization=org, is_active=True
            ).values_list('user_id', flat=True)

            return qs.filter(
                models.Q(organization=org) | models.Q(id__in=user_ids_via_access)
            ).distinct()

        # HO / RO / PIU / lower — same org visibility only
        org = user.organization
        if org is None:
            from access.models import UserOrgAccess
            access = UserOrgAccess.objects.filter(
                user=user, is_active=True
            ).select_related('org_unit__organization').first()
            if access:
                org = access.org_unit.organization
        if org:
            return qs.filter(organization=org)
        return qs.none()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "is_staff"]
    search_fields    = ["email", "full_name", "phone"]
    ordering_fields  = ["email", "full_name", "date_joined"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ("list", "create", "destroy"):
            return [IsAuthenticated(), IsAdminRole()]
        # retrieve, update, partial_update, me, set_password → self or admin
        return [IsAuthenticated(), IsSelfOrAdmin()]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """
        GET /api/v1/users/me/
        Returns the currently authenticated user's profile.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="set-password")
    def set_password(self, request, pk=None):
        """
        POST /api/v1/users/<id>/set-password/
        Body: {"password": "...", "password_confirm": "..."}
        """
        user = self.get_object()
        self.check_object_permissions(request, user)

        password = request.data.get("password", "")
        password_confirm = request.data.get("password_confirm", "")

        if not password:
            return Response(
                {"error": True, "message": "password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if password != password_confirm:
            return Response(
                {"error": True, "message": "Passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(password) < 8:
            return Response(
                {"error": True, "message": "Password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save(update_fields=["password"])
        return Response({"message": "Password updated successfully."})
