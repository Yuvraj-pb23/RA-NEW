import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from orgs.models import OrgUnit
from access.utils import get_descendant_units

ho_unit = OrgUnit.objects.filter(name="HO Unit").first()
print("HO Unit id:", ho_unit.pk)
units = get_descendant_units(ho_unit)
print("Descendants count:", units.count())

