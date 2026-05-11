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


# ── Custom Filters ────────────────────────────────────────────────────────────

class UUIDInFilter(django_filters.BaseInFilter, django_filters.UUIDFilter):
    pass

# ── FilterSet ─────────────────────────────────────────────────────────────────

class RoadFilter(django_filters.FilterSet):
    project      = UUIDInFilter(field_name="project__id")
    organization = UUIDInFilter(field_name="project__organization__id")
    ho_user      = django_filters.CharFilter(method="filter_ho_user")
    ro_user      = django_filters.CharFilter(method="filter_ro_user")
    piu_user     = django_filters.CharFilter(method="filter_piu_user")
    project_user = UUIDInFilter(field_name="project__project_user__id")
    road_type    = django_filters.CharFilter(field_name="road_type")
    name         = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model  = Road
        fields = ["project", "organization", "ho_user", "ro_user", "piu_user", "project_user", "road_type", "name"]

    def filter_ho_user(self, queryset, name, value):
        from accounts.models import User
        from access.utils import get_user_accessible_units
        ids = [v.strip() for v in value.split(',') if v.strip()]
        if not ids: return queryset
        
        q = Q()
        for v in ids:
            try:
                target_user = User.objects.get(id=v)
                accessible_units = get_user_accessible_units(target_user)
                # Combine OR for multiple users
                q |= (
                    Q(project__ho_user__id=v) |
                    Q(project__ro_user__ho_user__id=v) |
                    Q(project__piu_user__ho_user__id=v) |
                    Q(project__project_user__ho_user__id=v) |
                    Q(project__org_unit__in=accessible_units)
                )
            except (User.DoesNotExist, ValueError): continue
        return queryset.filter(q).distinct() if q else queryset.none()

    def filter_ro_user(self, queryset, name, value):
        from accounts.models import User
        from access.utils import get_user_accessible_units
        ids = [v.strip() for v in value.split(',') if v.strip()]
        if not ids: return queryset

        q = Q()
        for v in ids:
            try:
                target_user = User.objects.get(id=v)
                accessible_units = get_user_accessible_units(target_user)
                q |= (
                    Q(project__ro_user__id=v) |
                    Q(project__piu_user__ro_user__id=v) |
                    Q(project__project_user__ro_user__id=v) |
                    Q(project__org_unit__in=accessible_units)
                )
            except (User.DoesNotExist, ValueError): continue
        return queryset.filter(q).distinct() if q else queryset.none()

    def filter_piu_user(self, queryset, name, value):
        from accounts.models import User
        from access.utils import get_user_accessible_units
        ids = [v.strip() for v in value.split(',') if v.strip()]
        if not ids: return queryset

        q = Q()
        for v in ids:
            try:
                target_user = User.objects.get(id=v)
                accessible_units = get_user_accessible_units(target_user)
                q |= (
                    Q(project__piu_user__id=v) |
                    Q(project__project_user__piu_user__id=v) |
                    Q(project__org_unit__in=accessible_units)
                )
            except (User.DoesNotExist, ValueError): continue
        return queryset.filter(q).distinct() if q else queryset.none()


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
            final_qs = qs
        else:
            custom_role = getattr(user, 'custom_role', None)
            is_supervisor = custom_role and (getattr(custom_role, 'is_supervisor_role', False) or getattr(custom_role, 'has_supervisor_visibility', False))
            
            if role in [SystemRole.ORG_ADMIN, SystemRole.HO_USER] or is_supervisor:
                if user.organization:
                    final_qs = qs.filter(project__organization=user.organization)
                else:
                    final_qs = qs.none()
            else:
                accessible_units = get_user_accessible_units(user)
                visibility_q = Q(project__org_unit__in=accessible_units)
                
                if role == SystemRole.RO_USER:
                    visibility_q |= Q(project__ro_user=user)
                elif role == SystemRole.PIU_USER:
                    visibility_q |= Q(project__piu_user=user)
                elif role == SystemRole.PROJECT_USER:
                    visibility_q |= Q(project__project_user=user)
                    
                final_qs = qs.filter(visibility_q).distinct()

        if self.request.query_params.get('exclude_unassigned') == 'true':
            final_qs = final_qs.exclude(
                Q(project__ho_user__role=SystemRole.UNASSIGNED) |
                Q(project__ro_user__role=SystemRole.UNASSIGNED) |
                Q(project__piu_user__role=SystemRole.UNASSIGNED) |
                Q(project__project_user__role=SystemRole.UNASSIGNED) |
                Q(project__ho_user__isnull=True, project__ro_user__isnull=True, project__piu_user__isnull=True, project__project_user__isnull=True)
            )
        elif self.request.query_params.get('only_unassigned') == 'true':
            final_qs = final_qs.filter(
                Q(project__ho_user__role=SystemRole.UNASSIGNED) |
                Q(project__ro_user__role=SystemRole.UNASSIGNED) |
                Q(project__piu_user__role=SystemRole.UNASSIGNED) |
                Q(project__project_user__role=SystemRole.UNASSIGNED) |
                Q(project__ho_user__isnull=True, project__ro_user__isnull=True, project__piu_user__isnull=True, project__project_user__isnull=True)
            )

        return final_qs

    def perform_create(self, serializer):
        road = serializer.save()
        if road.gpx_file:
            self._process_gpx(road)
            road.refresh_from_db()
        if road.furniture_json_file:
            self._process_json(road, 'furniture')
            road.refresh_from_db()
        if road.pavement_json_file:
            self._process_json(road, 'pavement')
            road.refresh_from_db()
        if road.survey_zip:
            self._process_survey_zip(road)
            road.refresh_from_db()

    def perform_update(self, serializer):
        road = serializer.save()
        if 'gpx_file' in serializer.validated_data and road.gpx_file:
            self._process_gpx(road)
            road.refresh_from_db()
        if 'furniture_json_file' in serializer.validated_data and road.furniture_json_file:
            self._process_json(road, 'furniture')
            road.refresh_from_db()
        if 'pavement_json_file' in serializer.validated_data and road.pavement_json_file:
            self._process_json(road, 'pavement')
            road.refresh_from_db()
        if 'survey_zip' in serializer.validated_data and road.survey_zip:
            self._process_survey_zip(road)
            road.refresh_from_db()

    def _process_gpx(self, road):
        try:
            from .utils import parse_gpx
            data = parse_gpx(road.gpx_file.path)
            if data and "points" in data and len(data["points"]) >= 2:
                coords = [[pt["lng"], pt["lat"]] for pt in data["points"]]
                road.geometry = {
                    "type": "LineString",
                    "coordinates": coords
                }
                if road.length == 0 and "length_km" in data:
                    road.length = data["length_km"]
                road.save(update_fields=['geometry', 'length'])
        except Exception as e:
            print(f"Failed to process GPX for Road {road.id}: {e}")

    def _process_json(self, road, json_type):
        """Parse the uploaded JSON file and cache it in the corresponding json_data field.
        json_type: 'furniture' or 'pavement'
        """
        import json
        file_field = getattr(road, f'{json_type}_json_file', None)
        if not file_field:
            return
        try:
            with file_field.open('r') as f:
                parsed = json.load(f)
            setattr(road, f'{json_type}_json_data', parsed)
            road.save(update_fields=[f'{json_type}_json_data'])
        except Exception as e:
            print(f"Failed to parse {json_type} JSON for Road {road.id}: {e}")

    def _process_survey_zip(self, road):
        """Extract and process the uploaded survey ZIP folder."""
        import zipfile
        import json
        import os
        from django.core.files.base import ContentFile

        if not road.survey_zip:
            return

        try:
            with zipfile.ZipFile(road.survey_zip.path, 'r') as z:
                # 1. Process main_survey_data.json
                main_json_path = None
                for name in z.namelist():
                    if name.endswith('main_survey_data.json'):
                        main_json_path = name
                        break
                
                if main_json_path:
                    with z.open(main_json_path) as f:
                        main_data = json.load(f)
                    road.pavement_json_data = main_data
                    if 'road' in main_data and 'track_length' in main_data['road']:
                        road.length = round(float(main_data['road']['track_length']) / 1000.0, 3)
                    if 'road' in main_data and 'lat_lng' in main_data['road']:
                        coords = [[pt[1], pt[0]] for pt in main_data['road']['lat_lng']]
                        road.geometry = {"type": "LineString", "coordinates": coords}

                # 2. Extract and Process GPX File
                gpx_path = None
                for name in z.namelist():
                    if name.endswith('.gpx'):
                        gpx_path = name
                        break
                
                if gpx_path:
                    gpx_content = z.read(gpx_path)
                    gpx_filename = os.path.basename(gpx_path)
                    road.gpx_file.save(gpx_filename, ContentFile(gpx_content), save=False)
                    # After saving file, process it for geometry if we haven't already from JSON
                    # (GPX is usually more precise than JSON summary)
                    self._process_gpx(road)

                # 3. Look for Furniture_JSON and merge
                furniture_merged = {}
                for name in z.namelist():
                    if 'Furniture_JSON' in name and name.endswith('.json'):
                        with z.open(name) as f:
                            try:
                                f_data = json.load(f)
                                if isinstance(f_data, dict):
                                    for k, v in f_data.items():
                                        if k in furniture_merged and isinstance(v, list) and isinstance(furniture_merged[k], list):
                                            furniture_merged[k].extend(v)
                                        else:
                                            furniture_merged[k] = v
                            except: continue
                
                if furniture_merged:
                    road.furniture_json_data = furniture_merged

                road.save()
        except Exception as e:
            print(f"Failed to process survey ZIP for Road {road.id}: {e}")

from django.contrib.auth.decorators import login_required

@login_required
def road_gpx_view(request, road_id):
    try:
        from accounts.models import SystemRole
        from access.utils import get_user_accessible_units
        
        qs = Road.objects.all()
        
        custom_role = getattr(request.user, 'custom_role', None)
        is_supervisor = custom_role and (custom_role.is_supervisor_role or custom_role.has_supervisor_visibility)
        
        if request.user.role != SystemRole.SUPER_ADMIN:
            if request.user.role in [SystemRole.ORG_ADMIN, SystemRole.HO_USER] or is_supervisor:
                if request.user.organization:
                    qs = qs.filter(project__organization=request.user.organization)
                else:
                    qs = qs.none()
            else:
                accessible_units = get_user_accessible_units(request.user)
                visibility_q = Q(project__org_unit__in=accessible_units)
                
                if request.user.role == SystemRole.RO_USER:
                    visibility_q |= Q(project__ro_user=request.user)
                elif request.user.role == SystemRole.PIU_USER:
                    visibility_q |= Q(project__piu_user=request.user)
                elif request.user.role == SystemRole.PROJECT_USER:
                    visibility_q |= Q(project__project_user=request.user)
                    
                qs = qs.filter(visibility_q).distinct()
            
        road = qs.get(id=road_id)
        if road.gpx_file:
            data = parse_gpx(road.gpx_file.path)
            return JsonResponse(data)
        return JsonResponse({"error": "No GPX file found"}, status=404)
    except Road.DoesNotExist:
        return JsonResponse({"error": "Road not found"}, status=404)
