import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from orgs.models import Organization, OrgUnit, HierarchyLevel
from projects.models import Project
from roads.models import Road

def run():
    print("Creating dummy data...")
    org = Organization.objects.first()
    if not org:
        print("No organization found. Creating one...")
        org = Organization.objects.create(name="Default Org")
        HierarchyLevel.objects.create(organization=org, level_name="Project", level_depth=5)

    
    project_level = HierarchyLevel.objects.filter(organization=org, level_name__iexact="Project").first()
    if not project_level:
        project_level = HierarchyLevel.objects.create(organization=org, level_name="Project", level_depth=5)

    org_unit = OrgUnit.objects.filter(organization=org, level=project_level).first()
    if not org_unit:
        org_unit = OrgUnit.objects.create(name="Dummy Project Unit", organization=org, level=project_level)

    # Create Projects
    projects_data = [
        {"name": "Highway Expansion Alpha", "description": "Expanding highway from city A to city B."},
        {"name": "Bridge Renovation Beta", "description": "Renovating old bridge Beta."},
        {"name": "Rural Road Connectivity", "description": "Connecting several rural villages."},
        {"name": "Tunnel Construction", "description": "Tunnel through the mountains."},
        {"name": "City Ring Road", "description": "Ring road around the capital."},
    ]

    projects = []
    for p_data in projects_data:
        project, created = Project.objects.get_or_create(
            name=p_data["name"],
            organization=org,
            org_unit=org_unit,
            defaults={
                "description": p_data["description"]
            }
        )
        projects.append(project)

    # Create Roads
    roads_data = [
        {"name": "NH-42 Alpha segment", "road_type": "NH", "length": 150.5},
        {"name": "SH-15 Beta path", "road_type": "SH", "length": 45.2},
        {"name": "MDR-01 Rural", "road_type": "MDR", "length": 20.0},
        {"name": "ODR Tunnel Approach", "road_type": "ODR", "length": 5.5},
        {"name": "VR Ring Road link", "road_type": "VR", "length": 10.0},
        {"name": "NH-10 Expressway", "road_type": "NH", "length": 300.0},
    ]

    for i, r_data in enumerate(roads_data):
        Road.objects.get_or_create(
            name=r_data["name"],
            project=projects[i % len(projects)],
            defaults={
                "road_type": r_data["road_type"],
                "length": r_data["length"],
            }
        )
    print("Done adding dummy projects and roads.")

if __name__ == "__main__":
    run()

def assign_to_all_users():
    from accounts.models import User
    from access.models import UserOrgAccess
    
    org_unit = OrgUnit.objects.filter(name="Dummy Project Unit").first()
    if not org_unit: return
    
    users = User.objects.all()
    for u in users:
        # Give them access to this org unit so it shows up
        UserOrgAccess.objects.get_or_create(
            user=u,
            org_unit=org_unit,
            defaults={"role": "VIEWER"}
        )
    print("Assigned users to dummy org unit so projects show up.")

if __name__ == "__main__":
    assign_to_all_users()
