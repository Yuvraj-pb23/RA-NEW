import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from accounts.models import User
from access.models import UserOrgAccess
from access.utils import get_user_accessible_units

user = User.objects.get(email="ho@test.com")
print("User id:", user.pk)
print("User roles active:", UserOrgAccess.objects.filter(user=user, is_active=True).values('org_unit_id', 'role'))

accessible = get_user_accessible_units(user)
print("SQL output list:", type(accessible), accessible.count())
