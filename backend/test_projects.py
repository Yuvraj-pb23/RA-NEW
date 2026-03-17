import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from accounts.models import User
from projects.models import Project

user = User.objects.get(email='projectdelhi@gmail.com')
from access.utils import get_user_accessible_units

accessible_units = get_user_accessible_units(user)
print(f"Projects accessible by {user.email}:")
qs = Project.objects.filter(org_unit__in=accessible_units)
print(qs.count())
for p in qs:
    print(p.name, p.org_unit.name)

print("\nAll projects in DB:")
for p in Project.objects.all():
    print(f"Project: {p.name}, Org Unit: {p.org_unit.name if p.org_unit else 'No unit'}")
