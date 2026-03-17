import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User
from orgs.models import Organization
from orgs.models import OrgUnit, HierarchyLevel as OrgLevel
from access.models import UserOrgAccess

Organization.objects.all().delete()
#
#

django.setup()

org, _ = Organization.objects.get_or_create(name="Forest Dept")

ho_level, _ = OrgLevel.objects.get_or_create(level_name="HO", level_order=1, organization=org)
ro_level, _ = OrgLevel.objects.get_or_create(level_name="RO", level_order=2, parent_level=ho_level, organization=org)

# Create HO Unit directly
ho_unit, _ = OrgUnit.objects.get_or_create(
    organization=org,
    level=ho_level,
    name="Head Office"
)

# Test creating HO Admin User via serializer
from accounts.serializers import UserCreateSerializer
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()
request = factory.post('/api/v1/accounts/users/')

# We mock superuser here or so
user, _ = User.objects.get_or_create(username="super", role="SUPER_ADMIN", is_superuser=True)
request.user = user

data = {
    "username": "ho_admin2",
    "password": "password123",
    "role": "HO_USER",
    "organization": str(org.id),
    "first_name": "HO",
    "last_name": "Admin"
}

serializer = UserCreateSerializer(data=data, context={'request': request})
serializer.is_valid(raise_exception=True)
ho_user = serializer.save()

print("Created user:", ho_user.username, "Role:", ho_user.role)
access = UserOrgAccess.objects.filter(user=ho_user).first()
if access:
    print("Auto-assigned to unit:", access.org_unit.name, "Role:", access.role)
else:
    print("ERROR: No auto assignment found!")

# Now test the HO admin creating an RO unit
from orgs.serializers import OrgUnitSerializer

req2 = factory.post('/api/v1/orgs/units/')
req2.user = ho_user
setattr(req2.user, "org_accesses", UserOrgAccess.objects.filter(user=ho_user))

ro_data = {
    "organization": str(org.id),
    "level": str(ro_level.id),
    "name": "Regional Office 1",
    "parent_unit": str(ho_unit.id)
}

ro_serializer = OrgUnitSerializer(data=ro_data, context={'request': req2})
if ro_serializer.is_valid():
    ro_unit = ro_serializer.save()
    print("Successfully created RO unit:", ro_unit.name, "under", ro_unit.parent_unit.name)
else:
    print("Failed to create RO unit:", ro_serializer.errors)

# Try creating under another unit (should fail)
other_ho_unit, _ = OrgUnit.objects.get_or_create(
    organization=org,
    level=ho_level,
    name="Other Head Office"
)

bad_data = {
    "organization": str(org.id),
    "level": str(ro_level.id),
    "name": "Regional Office 2",
    "parent_unit": str(other_ho_unit.id)
}
bad_serializer = OrgUnitSerializer(data=bad_data, context={'request': req2})
if not bad_serializer.is_valid():
    print("Correctly prevented creating under sibling parent:", bad_serializer.errors)
else:
    print("FAILED! It allowed creating under a sibling HO unit where there's no access.")