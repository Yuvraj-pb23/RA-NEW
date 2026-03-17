import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model
from orgs.models import OrgUnit
from django.db import connection

User = get_user_model()
u = User.objects.get(email="rodelhi@gmail.com")

sql = """
    WITH RECURSIVE subtree AS (
        SELECT ou.id
        FROM   orgs_orgunit ou
        INNER  JOIN access_userorgaccess uoa
                 ON uoa.org_unit_id = ou.id
        WHERE  uoa.user_id = %s
          AND  uoa.is_active = 1

        UNION ALL

        SELECT child.id
        FROM   orgs_orgunit child
        INNER  JOIN subtree ON child.parent_unit_id = subtree.id
    )
    SELECT DISTINCT id FROM subtree;
"""
with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(access_userorgaccess);")
    print("cols:", cursor.fetchall())
    
    # Try different types
    try:
        cursor.execute(sql, [str(u.pk).replace('-','')])
        rows = cursor.fetchall()
        print("Without dashes:", rows)
    except Exception as e:
        print(e)
    
    try:
        cursor.execute(sql, [str(u.pk)])
        rows = cursor.fetchall()
        print("With dashes:", rows)
    except Exception as e:
        print(e)

