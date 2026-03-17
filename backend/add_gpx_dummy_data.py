import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from roads.models import Road
from projects.models import Project

project = Project.objects.first()

if project:
    Road.objects.create(
        name="SRL Road 8",
        project=project,
        gpx_file="gpx/20260212-112732_-_SRL_8.gpx"
    )

    Road.objects.create(
        name="SRL Road 9",
        project=project,
        gpx_file="gpx/20260225-131930_-_SRL_9.gpx"
    )
    print("Dummy data created.")
else:
    print("No project found to attach roads to.")
