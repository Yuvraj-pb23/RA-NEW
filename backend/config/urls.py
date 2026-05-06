"""
config/urls.py — root URL configuration
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView


def service_worker(request):
    """Serve a no-op service worker that immediately unregisters itself.
    Prevents 404 errors from browsers that cached an old SW registration.
    """
    js = """
// This service worker does nothing — it immediately unregisters itself
// to clean up any stale registrations from previous deployments.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => {
    event.waitUntil(self.registration.unregister());
});
"""
    return HttpResponse(js.strip(), content_type="application/javascript")

urlpatterns = [
    # ── Root: redirect straight to login ──────────────────────────────────
    path("", RedirectView.as_view(url="/dashboard/login/", permanent=False)),

    # ── Service worker (self-unregistering stub to silence 404s) ──────────
    path("sw.js", service_worker, name="service_worker"),

    # ── Django admin ──────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Projects API  ─────────────────────────────────────────────────────
    path("api/projects/", include("projects.urls")),
    # ── Roads API  ───────────────────────────────────────────────────────
    path("api/roads/", include("roads.urls")),
    # ── User Access API  ───────────────────────────────────────────────
    path("api/user-access/", include("access.urls")),
    # ── REST API  ─────────────────────────────────────────────────────────
    path("api/", include("api.urls", namespace="api")),

    # ── HTML dashboard  ───────────────────────────────────────────────────
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
]
