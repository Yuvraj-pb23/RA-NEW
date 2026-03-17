import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from accounts.models import User
from roads.models import Road
from access.utils import get_user_accessible_units

user = User.objects.get(email='projectdelhi@gmail.com')
units = get_user_accessible_units(user)
qs = Road.objects.filter(project__org_unit__in=units)
print("Roads for projectdelhi:", qs.count())
for r in qs:
    print(r.name, r.project.name, r.project.org_unit.name)

print("\nAll Roads:")
for r in Road.objects.all():
    print(r.name, r.project.name, r.project.org_unit.name if r.project.org_unit else 'None')
