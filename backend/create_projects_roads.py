import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from orgs.models import Organization, OrgUnit
from projects.models import Project
from roads.models import Road

org = Organization.objects.first()
if not org:
    org = Organization.objects.create(name="Default Org", description="Default")

org_unit = OrgUnit.objects.first()
if not org_unit:
    org_unit = OrgUnit.objects.create(name="Default Unit", organization=org)

project = Project.objects.filter(name="Test Project", organization=org).first()
if not project:
    project = Project.objects.create(
        name="Test Project",
        organization=org,
        org_unit=org_unit,
        description="For testing roads"
    )

def create_gpx(filename, content):
    with open(f"media/{filename}", "w") as f:
        f.write(content)

dummy_gpx = """<?xml version='1.0' encoding='UTF-8'?>
<gpx version="1.1" creator="Dummy">
  <trk>
    <name>Dummy Track</name>
    <trkseg>
      <trkpt lat="28.6139" lon="77.2090"><time>2023-01-01T00:00:00Z</time></trkpt>
      <trkpt lat="28.6149" lon="77.2100"><time>2023-01-01T00:01:00Z</time></trkpt>
      <trkpt lat="28.6159" lon="77.2110"><time>2023-01-01T00:02:00Z</time></trkpt>
    </trkseg>
  </trk>
</gpx>
"""

create_gpx("gpx/20260212-112732_-_SRL_8.gpx", dummy_gpx)
create_gpx("gpx/20260225-131930_-_SRL_9.gpx", dummy_gpx)

Road.objects.get_or_create(
    name="SRL Road 8",
    project=project,
    defaults={"gpx_file": "gpx/20260212-112732_-_SRL_8.gpx", "length": 1.5}
)

Road.objects.get_or_create(
    name="SRL Road 9",
    project=project,
    defaults={"gpx_file": "gpx/20260225-131930_-_SRL_9.gpx", "length": 2.5}
)
print("Created roads")

