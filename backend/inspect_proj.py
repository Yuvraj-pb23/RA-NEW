import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from projects.models import Project
p = Project.objects.get(name="Rewari to Delhi")
print(p.org_unit, p.org_unit.id if p.org_unit else None)
