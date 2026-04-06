from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView
from django.shortcuts import redirect
from accounts.models import SystemRole
from roads.models import Road
import logging

logger = logging.getLogger(__name__)


# ── Role helpers ─────────────────────────────────────────────────────────────

def check_role(user, allowed_roles):
    role = getattr(user, 'role', None)
    return role in allowed_roles


# ── Shared mixins ────────────────────────────────────────────────────────────

class DashboardMixin(LoginRequiredMixin):
    """Base class for all dashboard views."""
    login_url   = "/dashboard/login/"
    active_page = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['user_role'] = getattr(user, 'role', None)
        ctx['user_org']  = getattr(user, 'organization', None)
        ctx['active_page'] = self.active_page
        
        custom_role = getattr(user, 'custom_role', None)
        ctx['is_supervisor_user'] = bool(custom_role and (custom_role.is_supervisor_role or custom_role.has_supervisor_visibility))

        # Resolve the user's primary org unit label for the welcome banner
        try:
            from access.models import UserOrgAccess
            first_access = (
                UserOrgAccess.objects
                .filter(user=user, is_active=True)
                .select_related('org_unit', 'org_unit__level')
                .first()
            )
            ctx['user_unit'] = first_access.org_unit if first_access else None
        except Exception:
            ctx['user_unit'] = None

        # Inject org's dynamic custom roles (sorted by hierarchy_level) for every page
        # This lets templates replace hardcoded "HO User", "RO User", etc. labels
        try:
            from roles.models import Role
            import json
            org = getattr(user, 'organization', None)
            if org:
                hierarchy_roles = list(
                    Role.objects
                    .filter(organization=org, status='active', is_supervisor_role=False)
                    .exclude(hierarchy_level=None)
                    .order_by('hierarchy_level', 'role_name')
                    .values('id', 'role_name', 'hierarchy_level')[:4]
                )
                supervisor_roles = list(
                    Role.objects
                    .filter(organization=org, status='active', is_supervisor_role=True)
                    .order_by('role_name')
                    .values('id', 'role_name', 'hierarchy_level')
                )
            else:
                hierarchy_roles = []
                supervisor_roles = []

            # role_labels[0..3] = names for slot 1..4 (ho/ro/piu/project)
            ctx['org_role_labels'] = {
                0: hierarchy_roles[0]['role_name'] if len(hierarchy_roles) > 0 else 'HO',
                1: hierarchy_roles[1]['role_name'] if len(hierarchy_roles) > 1 else 'RO',
                2: hierarchy_roles[2]['role_name'] if len(hierarchy_roles) > 2 else 'PIU',
                3: hierarchy_roles[3]['role_name'] if len(hierarchy_roles) > 3 else 'Project',
            }
            ctx['org_hierarchy_roles'] = hierarchy_roles
            ctx['org_supervisor_roles'] = supervisor_roles
            # Explicitly convert UUIDs to str so json.dumps doesn't fail
            serializable_roles = [
                {'id': str(r['id']), 'role_name': r['role_name'], 'hierarchy_level': r['hierarchy_level']}
                for r in hierarchy_roles
            ]
            ctx['org_roles_json'] = json.dumps(serializable_roles)
        except Exception as e:
            logger.warning(f"DashboardMixin: failed to load org roles: {e}")
            ctx['org_role_labels'] = {0: 'HO', 1: 'RO', 2: 'PIU', 3: 'Project'}
            ctx['org_hierarchy_roles'] = []
            ctx['org_supervisor_roles'] = []
            ctx['org_roles_json'] = '[]'

        return ctx


class SuperAdminRequiredMixin:
    """Only SUPER_ADMIN may pass."""
    def dispatch(self, request, *args, **kwargs):
        if not check_role(request.user, [SystemRole.SUPER_ADMIN]):
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)


class OrgAdminRequiredMixin:
    """Only SUPER_ADMIN and ORG_ADMIN may pass (not HO and below)."""
    def dispatch(self, request, *args, **kwargs):
        if not check_role(request.user, [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]):
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)


class UpperTierRequiredMixin:
    """SUPER_ADMIN, ORG_ADMIN, HO_USER, and supervisor roles may pass."""
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        custom_role = getattr(user, 'custom_role', None)
        is_supervisor = custom_role and (custom_role.is_supervisor_role or custom_role.has_supervisor_visibility)
        
        if not (check_role(user, [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN, SystemRole.HO_USER]) or is_supervisor):
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)


# ── Views ────────────────────────────────────────────────────────────────────

class LandingView(TemplateView):
    """Public welcome page shown at /. Authenticated users skip straight to dashboard."""
    template_name = "landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)


class DashboardHomeView(DashboardMixin, TemplateView):
    template_name = "dashboard/home.html"
    active_page   = "home"

    def dispatch(self, request, *args, **kwargs):
        role = getattr(request.user, 'role', None)
        # All users BELOW Org Admin default to the GIS view
        # Org Admin and Super Admin land on the Home dashboard
        if role not in [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]:
            return redirect('dashboard:gis')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user_role = ctx['user_role']

        # Build stat cards per role — each role only sees what's relevant to them
        cards = []

        if user_role == SystemRole.SUPER_ADMIN:
            cards = [
                {
                    "label": "Organizations",
                    "url":   "/api/v1/organizations/",
                    "link":  "/dashboard/organizations/",
                    "bg":    "from-indigo-500 to-indigo-600",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>',
                },
                {
                    "label": "Org Admins",
                    "url":   "/api/v1/users/?role=ORG_ADMIN",
                    "link":  "/dashboard/users/",
                    "bg":    "from-violet-500 to-violet-600",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>',
                },
                {
                    "label": "Total Users",
                    "url":   "/api/v1/users/",
                    "link":  "/dashboard/users/",
                    "bg":    "from-amber-500 to-orange-500",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>',
                },
            ]

        elif user_role == SystemRole.ORG_ADMIN:
            cards = [
                {
                    "label": "Projects",
                    "url":   "/api/v1/projects/",
                    "link":  "/dashboard/projects/",
                    "bg":    "from-blue-500 to-blue-600",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>',
                },
                {
                    "label": "Roads",
                    "url":   "/api/v1/roads/",
                    "link":  "/dashboard/roads/",
                    "bg":    "from-teal-500 to-emerald-500",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/></svg>',
                },
                {
                    "label": "Users",
                    "url":   "/api/v1/users/",
                    "link":  "/dashboard/users/",
                    "bg":    "from-amber-500 to-orange-500",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>',
                },
            ]

        elif user_role == SystemRole.HO_USER:
            cards = [
                {
                    "label": "Projects",
                    "url":   "/api/v1/projects/",
                    "link":  "/dashboard/projects/",
                    "bg":    "from-blue-500 to-blue-600",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>',
                },
                {
                    "label": "Roads",
                    "url":   "/api/v1/roads/",
                    "link":  "/dashboard/roads/",
                    "bg":    "from-teal-500 to-emerald-500",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/></svg>',
                },
                {
                    "label": "Team Members",
                    "url":   "/api/v1/users/",
                    "link":  "/dashboard/users/",
                    "bg":    "from-amber-500 to-orange-500",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>',
                },
            ]

        elif user_role == SystemRole.RO_USER:
            cards = [
                {
                    "label": "Projects",
                    "url":   "/api/v1/projects/",
                    "link":  "/dashboard/projects/",
                    "bg":    "from-blue-500 to-blue-600",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>',
                },
                {
                    "label": "Roads",
                    "url":   "/api/v1/roads/",
                    "link":  "/dashboard/roads/",
                    "bg":    "from-teal-500 to-emerald-500",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/></svg>',
                },
            ]

        else:
            # PIU_USER, PROJECT_USER, CONTRACTOR — minimal view
            cards = [
                {
                    "label": "My Projects",
                    "url":   "/api/v1/projects/",
                    "link":  "/dashboard/projects/",
                    "bg":    "from-blue-500 to-blue-600",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>',
                },
                {
                    "label": "My Roads",
                    "url":   "/api/v1/roads/",
                    "link":  "/dashboard/roads/",
                    "bg":    "from-teal-500 to-emerald-500",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/></svg>',
                },
            ]

        ctx["stat_cards"] = cards
        return ctx


class OrganizationListView(SuperAdminRequiredMixin, DashboardMixin, TemplateView):
    template_name = "dashboard/organizations/list.html"
    active_page   = "organizations"


class HierarchyTreeView(OrgAdminRequiredMixin, DashboardMixin, TemplateView):
    template_name = "dashboard/hierarchy/tree.html"
    active_page   = "hierarchy"


class OrgUnitListView(OrgAdminRequiredMixin, DashboardMixin, TemplateView):
    template_name = "dashboard/org_units/list.html"
    active_page   = "org_units"


class ProjectListView(DashboardMixin, TemplateView):
    template_name = "dashboard/projects/list.html"
    active_page   = "projects"


class RoadListView(DashboardMixin, TemplateView):
    template_name = "dashboard/roads/list.html"
    active_page   = "roads"


class UserListView(UpperTierRequiredMixin, DashboardMixin, TemplateView):
    template_name = "dashboard/users/list.html"
    active_page   = "users"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        oid = getattr(self.request.user, "organization_id", None)
        ctx["org_id"] = str(oid) if oid else ""
        return ctx


class AccessListView(OrgAdminRequiredMixin, DashboardMixin, TemplateView):
    template_name = "dashboard/access/list.html"
    active_page   = "access"


class RoleManagementView(OrgAdminRequiredMixin, DashboardMixin, TemplateView):
    """Role Management — accessible only to Org Admin and Super Admin."""
    template_name = "dashboard/roles/list.html"
    active_page   = "roles"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['org_id'] = str(user.organization_id) if user.organization_id else ''
        ctx['org_name'] = user.organization.name if user.organization else ''
        return ctx


class GISMapView(DashboardMixin, TemplateView):
    template_name = "dashboard/gis.html"
    active_page   = "gis"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Expose a generic Maps API key to the template (backend name-agnostic)
        try:
            from django.conf import settings
            ctx["maps_api_key"] = getattr(settings, "MAPS_API_KEY", "")
        except Exception:
            ctx["maps_api_key"] = ""
        from accounts.models import User, SystemRole
        from access.models import UserOrgAccess

        user = self.request.user
        base_qs = User.objects.filter(is_active=True)
        if getattr(user, 'organization', None):
            base_qs = base_qs.filter(organization=user.organization)

        ctx['show_ho_filter'] = base_qs.filter(role=SystemRole.HO_USER).exists()
        ctx['show_ro_filter'] = base_qs.filter(role=SystemRole.RO_USER).exists()
        ctx['show_piu_filter'] = base_qs.filter(role=SystemRole.PIU_USER).exists()
        ctx['show_project_filter'] = base_qs.filter(role=SystemRole.PROJECT_USER).exists()

        # Dynamic role filters from the roles table
        try:
            from roles.models import Role
            if getattr(user, 'organization', None):
                custom_role = getattr(user, 'custom_role', None)
                is_supervisor = (
                    custom_role is not None and
                    (custom_role.is_supervisor_role or custom_role.has_supervisor_visibility)
                )
                is_org_admin = getattr(user, 'role', None) in ('ORG_ADMIN', 'SUPER_ADMIN')

                roles_qs = Role.objects.filter(
                    organization=user.organization,
                    status='active'
                ).order_by('is_supervisor_role', 'hierarchy_level', 'role_name')

                if not is_supervisor and not is_org_admin and custom_role:
                    if not custom_role.is_supervisor_role and custom_role.hierarchy_level is not None:
                        # Show only roles at this level and below (higher level numbers)
                        roles_qs = roles_qs.filter(
                            is_supervisor_role=False,
                            hierarchy_level__gte=custom_role.hierarchy_level,
                        )

                ctx['dynamic_roles'] = list(
                    roles_qs.values('id', 'role_name', 'hierarchy_level', 'is_supervisor_role')
                )
                ctx['user_has_supervisor_filter'] = is_supervisor or is_org_admin
            else:
                ctx['dynamic_roles'] = []
                ctx['user_has_supervisor_filter'] = False
        except Exception:
            ctx['dynamic_roles'] = []
            ctx['user_has_supervisor_filter'] = False
        
        role = getattr(user, 'role', None)
        lock_ho_filter = False
        lock_ro_filter = False
        lock_piu_filter = False
        lock_project_filter = False
        
        assigned_ho = ""
        assigned_ro = ""
        assigned_piu = ""
        assigned_project = ""
        
        assigned_ho_name = ""
        assigned_ro_name = ""
        assigned_piu_name = ""
        assigned_project_name = ""

        is_supervisor = ctx.get('is_supervisor_user', False)

        if not is_supervisor:
            if role == SystemRole.HO_USER:
                lock_ho_filter = True
                assigned_ho = str(user.id)
                assigned_ho_name = user.display_name
                    
            elif role == SystemRole.RO_USER:
                lock_ho_filter = True
                lock_ro_filter = True
                assigned_ro = str(user.id)
                assigned_ro_name = user.display_name
                ho_u = User.objects.filter(role=SystemRole.HO_USER, organization=user.organization, is_active=True).first()
                if ho_u:
                    assigned_ho = str(ho_u.id)
                    assigned_ho_name = ho_u.display_name
                        
            elif role == SystemRole.PIU_USER:
                lock_ho_filter = True
                lock_ro_filter = True
                lock_piu_filter = True
                assigned_piu = str(user.id)
                assigned_piu_name = user.display_name
                ro_u = User.objects.filter(role=SystemRole.RO_USER, organization=user.organization, is_active=True).first()
                if ro_u:
                    assigned_ro = str(ro_u.id)
                    assigned_ro_name = ro_u.display_name
                ho_u = User.objects.filter(role=SystemRole.HO_USER, organization=user.organization, is_active=True).first()
                if ho_u:
                    assigned_ho = str(ho_u.id)
                    assigned_ho_name = ho_u.display_name

            elif role == SystemRole.PROJECT_USER:
                lock_ho_filter = True
                lock_ro_filter = True
                lock_piu_filter = True
                lock_project_filter = True
                assigned_project = str(user.id)
                assigned_project_name = user.display_name
                piu_u = User.objects.filter(role=SystemRole.PIU_USER, organization=user.organization, is_active=True).first()
                if piu_u:
                    assigned_piu = str(piu_u.id)
                    assigned_piu_name = piu_u.display_name
                ro_u = User.objects.filter(role=SystemRole.RO_USER, organization=user.organization, is_active=True).first()
                if ro_u:
                    assigned_ro = str(ro_u.id)
                    assigned_ro_name = ro_u.display_name
                ho_u = User.objects.filter(role=SystemRole.HO_USER, organization=user.organization, is_active=True).first()
                if ho_u:
                    assigned_ho = str(ho_u.id)
                    assigned_ho_name = ho_u.display_name

        ctx['lock_ho_filter'] = lock_ho_filter
        ctx['lock_ro_filter'] = lock_ro_filter
        ctx['lock_piu_filter'] = lock_piu_filter
        ctx['lock_project_filter'] = lock_project_filter
        ctx['assigned_ho'] = assigned_ho
        ctx['assigned_ro'] = assigned_ro
        ctx['assigned_piu'] = assigned_piu
        ctx['assigned_project'] = assigned_project
        ctx['assigned_ho_name'] = assigned_ho_name
        ctx['assigned_ro_name'] = assigned_ro_name
        ctx['assigned_piu_name'] = assigned_piu_name
        ctx['assigned_project_name'] = assigned_project_name
        
        return ctx


class RoadDetailView(DashboardMixin, DetailView):
    model = Road
    template_name = "dashboard/roads/road_detail.html"
    active_page = "roads"
    context_object_name = "road"
    pk_url_kwarg = "road_id"

    def get_queryset(self):
        qs = super().get_queryset()
        from accounts.models import SystemRole
        from access.utils import get_user_accessible_units
        from django.db.models import Q
        
        user = self.request.user
        role = getattr(user, 'role', None)
        
        if role == SystemRole.SUPER_ADMIN:
            return qs
            
        custom_role = getattr(user, 'custom_role', None)
        is_supervisor = custom_role and (custom_role.is_supervisor_role or custom_role.has_supervisor_visibility)
            
        if role in [SystemRole.ORG_ADMIN, SystemRole.HO_USER] or is_supervisor:
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
