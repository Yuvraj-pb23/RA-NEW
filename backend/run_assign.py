import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from orgs.models import OrgUnit
from projects.models import Project
from accounts.models import User
from access.models import UserOrgAccess

def run():
    projects = Project.objects.all()
    org_units = set(p.org_unit for p in projects)
    
    users = User.objects.all()
    for u in users:
        for ou in org_units:
            UserOrgAccess.objects.get_or_create(user=u, org_unit=ou, defaults={"role": "VIEWER"})
    print(f"Assigned all {users.count()} users to {len(org_units)} org units.")

run()
