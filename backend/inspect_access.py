import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from access.utils import get_user_accessible_units
from accounts.models import User

users = User.objects.exclude(role='SUPER_ADMIN')
print(f"Found {users.count()} non-superadmin users")
for user in users:
    print(f"User: {user.email}, Role: {user.role}, OrgAssigned: {user.organization_id}")
    units = get_user_accessible_units(user)
    print(f"Accessible units count: {units.count()}")
