import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from orgs.models import OrgUnit
qs = OrgUnit.objects.all()
if qs.exists():
    obj = qs.first()
    print("obj in qs:", obj in qs)
    print("obj.id in qs:", obj.id in qs)
