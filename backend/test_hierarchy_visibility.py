import os
import django
import uuid

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from orgs.models import Organization, HierarchyLevel, OrgUnit
from access.models import UserOrgAccess
from projects.models import Project
from roads.models import Road
from accounts.models import SystemRole

User = get_user_model()

def run_test():
    print("Starting hierarchy visibility test...")
    
    # 1. Setup Organization and Hierarchy
    org, _ = Organization.objects.get_or_create(name="Test Org Visibility")
    
    ho_level, _ = HierarchyLevel.objects.get_or_create(organization=org, level_name="HO", level_order=1)
    ro_level, _ = HierarchyLevel.objects.get_or_create(organization=org, level_name="RO", level_order=2, parent_level=ho_level)
    piu_level, _ = HierarchyLevel.objects.get_or_create(organization=org, level_name="PIU", level_order=3, parent_level=ro_level)
    proj_level, _ = HierarchyLevel.objects.get_or_create(organization=org, level_name="Project", level_order=4, parent_level=piu_level)
    
    ho_unit, _ = OrgUnit.objects.get_or_create(organization=org, name="HO North", level=ho_level)
    ro_unit, _ = OrgUnit.objects.get_or_create(organization=org, name="RO Agra", level=ro_level, parent_unit=ho_unit)
    piu_unit, _ = OrgUnit.objects.get_or_create(organization=org, name="PIU Mathura", level=piu_level, parent_unit=ro_unit)
    proj_unit, _ = OrgUnit.objects.get_or_create(organization=org, name="Project Road 1", level=proj_level, parent_unit=piu_unit)
    
    # 2. Setup Users
    org_admin, _ = User.objects.get_or_create(
        email="orgadmin@test.com", 
        defaults={"role": SystemRole.ORG_ADMIN, "organization": org}
    )
    if _ : org_admin.set_password("password123"); org_admin.save()
    
    ho_user, _ = User.objects.get_or_create(
        email="ho_user@test.com", 
        defaults={"role": SystemRole.HO_USER, "organization": org}
    )
    if _ : ho_user.set_password("password123"); ho_user.save()
    
    # Assign HO User to HO Unit
    UserOrgAccess.objects.get_or_create(user=ho_user, org_unit=ho_unit, role="ho")
    
    # 3. Create Project as Org Admin (Unassigned User FIELDS)
    project, created = Project.objects.get_or_create(
        name="Agra-Mathura Expressway",
        organization=org,
        defaults={
            "org_unit": proj_unit,
            "description": "Created by Org Admin, unassigned to specific users",
            "ho_user": None,
            "ro_user": None,
            "piu_user": None,
            "project_user": None
        }
    )
    if not created:
        project.ho_user = None
        project.save()
        
    print(f"Project '{project.name}' created in unit '{proj_unit.name}' (under '{ho_unit.name}').")
    
    # 4. Verify Visibility for HO User
    from access.utils import get_user_accessible_units
    accessible_units = get_user_accessible_units(ho_user)
    
    print(f"HO User '{ho_user.email}' has access to {accessible_units.count()} units.")
    
    # Check if project unit is in accessible units
    if proj_unit in accessible_units:
        print("SUCCESS: Project unit is in HO user's accessible units.")
    else:
        print("FAILURE: Project unit is NOT in HO user's accessible units.")
        return

    # 5. Check queryset filtering logic (Manual check of what we implemented)
    projects_for_ho = Project.objects.filter(org_unit__in=accessible_units)
    if project in projects_for_ho:
        print("SUCCESS: Project is visible in filtered queryset for HO user.")
    else:
        print("FAILURE: Project is NOT visible in filtered queryset for HO user.")
        
    # 6. Check filter_ho_user logic
    from django.db.models import Q
    value = ho_user.id
    # Simulate our new filter_ho_user logic
    filtered_qs = Project.objects.filter(
        Q(ho_user__id=value) |
        Q(ro_user__ho_user__id=value) |
        Q(piu_user__ho_user__id=value) |
        Q(project_user__ho_user__id=value) |
        Q(org_unit__in=accessible_units)
    ).distinct()
    
    if project in filtered_qs:
        print("SUCCESS: Project is visible when applying ho_user filter.")
    else:
        print("FAILURE: Project is NOT visible when applying ho_user filter.")

if __name__ == "__main__":
    run_test()
