import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection

user_id = "02f6ddfa-f2ce-4306-a887-96525c029a2b"

sql = """
    SELECT ou.id
    FROM   orgs_orgunit ou
    INNER  JOIN access_userorgaccess uoa
             ON uoa.org_unit_id = ou.id
    WHERE  uoa.user_id  = %s
"""
with connection.cursor() as cursor:
    cursor.execute(sql, [user_id])
    print("Wait for string UUID:", cursor.fetchall())

sql_uuid = """
    SELECT ou.id
    FROM   orgs_orgunit ou
    INNER  JOIN access_userorgaccess uoa
             ON uoa.org_unit_id = ou.id
    WHERE  uoa.user_id  = %s
"""
user_uuid = "02f6ddfa-f2ce-4306-a887-96525c029a2b" # SQLite stores UUIDs without hyphens sometimes?
with connection.cursor() as cursor:
    cursor.execute(sql_uuid, [user_uuid.replace("-", "")])
    print("Without hyphens:", cursor.fetchall())

