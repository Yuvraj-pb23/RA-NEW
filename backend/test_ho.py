import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from accounts.models import User, SystemRole
from orgs.models import Organization, HierarchyLevel, OrgUnit
from access.models import UserOrgAccess
from access.utils import get_user_accessible_units

org = Organization.objects.filter(name="Test Org").first()

h1, _ = HierarchyLevel.objects.get_or_create(organization=org, level_name="HO", level_order=1)
h2, _ = HierarchyLevel.objects.get_or_create(organization=org, level_name="RO", level_order=2, parent_level=h1)

ho_unit = OrgUnit.objects.filter(organization=org, name="HO Unit").first()
ro_unit = OrgUnit.objects.filter(organization=org, name="RO Unit").first()

user, _ = User.objects.get_or_create(email="ho@test.com", organization=org, role=SystemRole.HO_USER)
access, _ = UserOrgAccess.objects.get_or_create(user=user, org_unit=ho_unit, role=UserOrgAccess.RoleChoices.HO)

accessible = get_user_accessible_units(user)
print("Accessible units:", list(accessible.values_list('name', flat=True)))
print("HO Unit in accessible?", accessible.filter(id=ho_unit.id).exists())
print("RO Unit in accessible?", accessible.filter(id=ro_unit.id).exists())
