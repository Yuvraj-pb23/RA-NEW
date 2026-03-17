import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(email="rodelhi@gmail.com")
print(u, u.role)
from access.utils import get_user_accessible_units
units = get_user_accessible_units(u)
print("Units:", units)

from projects.models import Project
from roads.models import Road

print("All projects:", Project.objects.all())
print("User projects:", Project.objects.filter(org_unit__in=units))

