import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from orgs.models import OrgUnit
from access.utils import get_descendant_units

ho_unit = OrgUnit.objects.filter(name="HO Unit").first()
print("HO Unit id:", ho_unit.pk.hex)

from django.db import connection

sql = """
    WITH RECURSIVE subtree AS (
        SELECT id
        FROM   orgs_orgunit
        WHERE  id = %s

        UNION ALL

        SELECT child.id
        FROM   orgs_orgunit child
        INNER JOIN subtree parent ON child.parent_unit_id = parent.id
    )
    SELECT id FROM subtree;
"""
with connection.cursor() as cursor:
    cursor.execute(sql, [ho_unit.pk.hex])
    rows = cursor.fetchall()
print([row[0] for row in rows])
