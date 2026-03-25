"""
dashboard/urls.py
=================
HTML dashboard URL patterns — session-authenticated.

URL layout
----------
  /dashboard/              → Home / overview
  /dashboard/login/        → Login form
  /dashboard/logout/       → Log out
  /dashboard/organizations/→ Organizations list
  /dashboard/hierarchy/    → Hierarchy tree viewer
  /dashboard/org-units/    → Org Units list
  /dashboard/projects/     → Projects list
  /dashboard/roads/        → Roads list
  /dashboard/users/        → Users list
  /dashboard/access/       → Access Control list
"""
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from dashboard.views import (
    AccessListView,
    DashboardHomeView,
    GISMapView,
    HierarchyTreeView,
    OrganizationListView,
    OrgUnitListView,
    ProjectListView,
    RoadListView,
    RoadDetailView,
    UserListView,
)

app_name = "dashboard"

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────
    path(
        "login/",
        LoginView.as_view(
            template_name="dashboard/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(next_page="/"),
        name="logout",
    ),

    # ── Dashboard pages ────────────────────────────────────────────────────
    path("",                  DashboardHomeView.as_view(),     name="home"),
    path("organizations/",    OrganizationListView.as_view(),  name="organizations"),
    # path("hierarchy/",        HierarchyTreeView.as_view(),     name="hierarchy"),
    # path("org-units/",        OrgUnitListView.as_view(),       name="org_units"),
    path("projects/",         ProjectListView.as_view(),       name="projects"),
    path("roads/",            RoadListView.as_view(),          name="roads"),
    path("roads/<uuid:road_id>/view/", RoadDetailView.as_view(), name="road_detail"),
    path("gis/",              GISMapView.as_view(),            name="gis"),

    path("users/",            UserListView.as_view(),          name="users"),
    # path("access/",           AccessListView.as_view(),        name="access"),
]
