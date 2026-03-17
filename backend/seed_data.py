import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from orgs.models import Organization
from accounts.models import User, SystemRole

def seed():
    nhai, _ = Organization.objects.get_or_create(name="NHAI", defaults={'country': 'India', 'description': 'NHAI', 'is_active': True})
    pwd, _ = Organization.objects.get_or_create(name="PWD", defaults={'country': 'India', 'description': 'PWD', 'is_active': True})

    users_data = [
        {"email": "ho@nhai.com", "role": SystemRole.HO_USER, "org": nhai, "first_name": "NHAI HO"},
        {"email": "ro@nhai.com", "role": SystemRole.RO_USER, "org": nhai, "first_name": "NHAI RO"},
        {"email": "piu@nhai.com", "role": SystemRole.PIU_USER, "org": nhai, "first_name": "NHAI PIU"},
        {"email": "ho@pwd.com", "role": SystemRole.HO_USER, "org": pwd, "first_name": "PWD HO"},
        {"email": "ro@pwd.com", "role": SystemRole.RO_USER, "org": pwd, "first_name": "PWD RO"},
        {"email": "piu@pwd.com", "role": SystemRole.PIU_USER, "org": pwd, "first_name": "PWD PIU"},
    ]

    for ud in users_data:
        u, created = User.objects.get_or_create(
            email=ud['email'],
            defaults={
                
                "role": ud['role'],
                "organization": ud['org'],
                "full_name": ud['first_name']
            }
        )
        if created:
            u.set_password("password123")
            u.save()
            print(f"Created user {u.email}")
        else:
            u.role = ud['role']
            u.organization = ud['org']
            u.set_password("password123")
            u.save()
            print(f"Updated user {u.email}")

if __name__ == '__main__':
    seed()
