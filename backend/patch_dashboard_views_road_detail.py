import os

with open('dashboard/views.py', 'r') as f:
    content = f.read()

# Make sure DetailView is imported
if 'from django.views.generic import TemplateView, DetailView' not in content:
    content = content.replace('from django.views.generic import TemplateView', 'from django.views.generic import TemplateView, DetailView')

# Ensure Road is imported for DetailView
if 'from roads.models import Road' not in content:
    content = content.replace('from accounts.models import SystemRole', 'from accounts.models import SystemRole\nfrom roads.models import Road')


new_view = """
class RoadDetailView(DashboardMixin, DetailView):
    model = Road
    template_name = "dashboard/roads/road_detail.html"
    active_page = "roads"
    context_object_name = "road"
    pk_url_kwarg = "road_id"
"""

if 'class RoadDetailView' not in content:
    content += "\n" + new_view

with open('dashboard/views.py', 'w') as f:
    f.write(content)

