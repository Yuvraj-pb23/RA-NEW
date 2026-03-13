"""
dashboard/views.py
==================
Thin, session-authenticated views for the HTML dashboard.

Design principle:
  Views pass minimal context to templates.
  All live data is loaded by the template via fetch() → /api/v1/ endpoints.
  Views are responsible only for: auth check, page title, active nav, and
  any server-side context the template cannot self-load.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


# ── Shared mixin ──────────────────────────────────────────────────────────────

class DashboardMixin(LoginRequiredMixin):
    """
    Base class for all dashboard views.

    Subclasses set:
        active_page  — matches sidebar nav keys: home, organizations, hierarchy,
                       org_units, projects, roads, users, access
        page_title   — shown in topbar
    """
    login_url    = "/dashboard/login/"
    active_page  = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = self.active_page
        return ctx


# ── Views ────────────────────────────────────────────────────────────────────

class DashboardHomeView(DashboardMixin, TemplateView):
    template_name = "dashboard/home.html"
    active_page   = "home"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Stat cards: each card fetches its own count via Alpine.js statCard()
        ctx["stat_cards"] = [
            {
                "label": "Organizations",
                "url":   "/api/v1/organizations/",
                "link":  "/dashboard/organizations/",
                "bg":    "bg-indigo-100",
                "text":  "text-indigo-600",
                "icon":  '<svg class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>',
            },
            {
                "label": "Org Units",
                "url":   "/api/v1/org-units/",
                "link":  "/dashboard/org-units/",
                "bg":    "bg-violet-100",
                "text":  "text-violet-600",
                "icon":  '<svg class="w-5 h-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
            },
            {
                "label": "Projects",
                "url":   "/api/v1/projects/",
                "link":  "/dashboard/projects/",
                "bg":    "bg-blue-100",
                "text":  "text-blue-600",
                "icon":  '<svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>',
            },
            {
                "label": "Roads",
                "url":   "/api/v1/roads/",
                "link":  "/dashboard/roads/",
                "bg":    "bg-teal-100",
                "text":  "text-teal-600",
                "icon":  '<svg class="w-5 h-5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20H5a2 2 0 01-2-2V6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M9 20l2-2m-2 2l2 2"/></svg>',
            },
            {
                "label": "Users",
                "url":   "/api/v1/users/",
                "link":  "/dashboard/users/",
                "bg":    "bg-amber-100",
                "text":  "text-amber-600",
                "icon":  '<svg class="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>',
            },
            {
                "label": "Access Grants",
                "url":   "/api/v1/user-access/",
                "link":  "/dashboard/access/",
                "bg":    "bg-rose-100",
                "text":  "text-rose-600",
                "icon":  '<svg class="w-5 h-5 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>',
            },
        ]
        return ctx


class OrganizationListView(DashboardMixin, TemplateView):
    template_name = "dashboard/organizations/list.html"
    active_page   = "organizations"


class HierarchyTreeView(DashboardMixin, TemplateView):
    template_name = "dashboard/hierarchy/tree.html"
    active_page   = "hierarchy"


class OrgUnitListView(DashboardMixin, TemplateView):
    template_name = "dashboard/org_units/list.html"
    active_page   = "org_units"


class ProjectListView(DashboardMixin, TemplateView):
    template_name = "dashboard/projects/list.html"
    active_page   = "projects"


class RoadListView(DashboardMixin, TemplateView):
    template_name = "dashboard/roads/list.html"
    active_page   = "roads"


class UserListView(DashboardMixin, TemplateView):
    template_name = "dashboard/users/list.html"
    active_page   = "users"


class AccessListView(DashboardMixin, TemplateView):
    template_name = "dashboard/access/list.html"
    active_page   = "access"
