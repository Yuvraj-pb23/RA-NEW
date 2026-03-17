from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView
from django.shortcuts import redirect
from accounts.models import SystemRole
from roads.models import Road


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
    """SUPER_ADMIN, ORG_ADMIN, and HO_USER may pass."""
    def dispatch(self, request, *args, **kwargs):
        if not check_role(request.user, [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN, SystemRole.HO_USER]):
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
        # HO users live in the GIS view — redirect them straight there
        if getattr(request.user, 'role', None) == SystemRole.HO_USER:
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
                {
                    "label": "Access Grants",
                    "url":   "/api/v1/user-access/",
                    "link":  "/dashboard/access/",
                    "bg":    "from-rose-500 to-rose-600",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>',
                },
            ]

        elif user_role == SystemRole.ORG_ADMIN:
            cards = [
                {
                    "label": "Org Units",
                    "url":   "/api/v1/org-units/",
                    "link":  "/dashboard/org-units/",
                    "bg":    "from-violet-500 to-violet-600",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"/></svg>',
                },
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
                {
                    "label": "Assignments",
                    "url":   "/api/v1/user-access/",
                    "link":  "/dashboard/access/",
                    "bg":    "from-rose-500 to-rose-600",
                    "icon":  '<svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>',
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


class AccessListView(OrgAdminRequiredMixin, DashboardMixin, TemplateView):
    template_name = "dashboard/access/list.html"
    active_page   = "access"


class GISMapView(UpperTierRequiredMixin, DashboardMixin, TemplateView):
    template_name = "dashboard/gis.html"
    active_page   = "gis"


class RoadDetailView(DashboardMixin, DetailView):
    model = Road
    template_name = "dashboard/roads/road_detail.html"
    active_page = "roads"
    context_object_name = "road"
    pk_url_kwarg = "road_id"

    def get_queryset(self):
        qs = super().get_queryset()
        user_role = getattr(self.request.user, 'role', None)
        if user_role == SystemRole.SUPER_ADMIN:
            return qs
        from access.utils import get_user_accessible_units
        accessible_units = get_user_accessible_units(self.request.user)
        return qs.filter(project__org_unit__in=accessible_units)
