import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from access.models import UserOrgAccess
for a in UserOrgAccess.objects.all():
    print(a.user, a.org_unit, a.is_active)

