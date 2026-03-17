import django
import os
from decimal import Decimal
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from projects.models import Project
from roads.models import Road

p = Project.objects.get(name='Rewari to Delhi')
Road.objects.create(name='New Assigned Road', project=p, length=Decimal('10.0'))
print("Created road for Rewari to Delhi")
