import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from access.utils import get_user_accessible_units
from access.models import UserOrgAccess
from accounts.models import User

users = User.objects.exclude(role='SUPER_ADMIN')
for user in users:
    print(f"\nUser: {user.email}")
    accesses = UserOrgAccess.objects.filter(user=user)
    print("Direct assignments:")
    for a in accesses:
        print(f"  - {a.org_unit.name} (Level: {a.org_unit.level.level_name})")
    
    units = get_user_accessible_units(user)
    print("Accessible units (via get_user_accessible_units):")
    for u in units:
        print(f"  - {u.name} (Level: {u.level.level_name})")
