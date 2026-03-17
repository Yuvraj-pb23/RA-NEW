import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from orgs.models import OrgUnit
for u in OrgUnit.objects.all():
    print(f"Name: {u.name}, Level: {u.level.level_name if u.level else 'None'}, Parent: {u.parent_unit.name if u.parent_unit else 'None'}, Org: {u.organization.name}")
