from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from orgs.models import Organization, OrgUnit
from projects.models import Project
from roads.models import Road
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({
            "total_organizations": Organization.objects.count(),
            "total_org_units": OrgUnit.objects.count(),
            "total_projects": Project.objects.count(),
            "total_roads": Road.objects.count(),
            "total_users": User.objects.count(),
        })
