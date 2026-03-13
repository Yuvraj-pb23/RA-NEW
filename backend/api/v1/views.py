"""
api/v1/views.py
===============
Standalone API views that don't belong to any specific app's ViewSet.
"""
from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orgs.models import Organization, OrgUnit
from projects.models import Project
from roads.models import Road


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    GET /api/v1/dashboard/
    Returns aggregate counts used by the dashboard home page.
    """
    total_length = Road.objects.aggregate(t=Sum("length"))["t"] or 0

    return Response(
        {
            "total_organizations": Organization.objects.count(),
            "total_org_units": OrgUnit.objects.count(),
            "total_projects": Project.objects.count(),
            "total_roads": Road.objects.count(),
            "total_users": get_user_model().objects.count(),
            "total_length_km": float(total_length),
        }
    )
