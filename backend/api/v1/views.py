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
from access.utils import get_user_accessible_units


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    GET /api/v1/dashboard/
    Returns aggregate counts used by the dashboard home page.
    """
    user = request.user
    
    if user.role == "SUPER_ADMIN":
        org_q = Organization.objects.all()
        # org_unit counts from all
        ou_q = OrgUnit.objects.all()
        proj_q = Project.objects.all()
        road_q = Road.objects.all()
        user_q = get_user_model().objects.all()
    else:
        accessible_units = get_user_accessible_units(user)
        # Assuming non-superusers can only see their organization's units/users
        # But specifically they only see projects/roads in their accessible units
        org_q = Organization.objects.filter(id=user.organization_id) if user.organization_id else Organization.objects.none()
        ou_q = accessible_units
        proj_q = Project.objects.filter(org_unit__in=accessible_units)
        road_q = Road.objects.filter(project__org_unit__in=accessible_units)
        user_q = get_user_model().objects.filter(organization_id=user.organization_id) if user.organization_id else get_user_model().objects.none()

    total_length = road_q.aggregate(t=Sum("length"))["t"] or 0

    return Response(
        {
            "total_organizations": org_q.count(),
            "total_org_units": ou_q.count(),
            "total_projects": proj_q.count(),
            "total_roads": road_q.count(),
            "total_users": user_q.count(),
            "total_length_km": float(total_length),
        }
    )
