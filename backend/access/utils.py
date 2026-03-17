from orgs.models import OrgUnit
from access.models import UserOrgAccess
from django.db import connection

def get_descendant_units(org_unit):
    """
    Recursive function to get all child OrgUnits.
    Uses Postgres recursive CTE for performance.
    """
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
        cursor.execute(sql, [org_unit.pk.hex])
        rows = cursor.fetchall()
    
    ids = [str(row[0]) for row in rows]
    return OrgUnit.objects.filter(id__in=ids)

def get_user_accessible_units(user):
    """
    Gets all assigned units from UserOrgAccess and recursively fetches all child units.
    """
    from accounts.models import SystemRole
    if user.role == SystemRole.SUPER_ADMIN:
        return OrgUnit.objects.all()
    if user.role == SystemRole.ORG_ADMIN:
        return OrgUnit.objects.filter(organization=user.organization)

    sql = """
        WITH RECURSIVE subtree AS (
            -- Anchor: every OrgUnit the user is directly assigned to
            SELECT ou.id
            FROM   orgs_orgunit ou
            INNER  JOIN access_userorgaccess uoa
                     ON uoa.org_unit_id = ou.id
            WHERE  uoa.user_id  = %s
              AND  uoa.is_active = TRUE

            UNION ALL

            -- Recursive step: pull in every child of an already-found unit
            SELECT child.id
            FROM   orgs_orgunit child
            INNER  JOIN subtree ON child.parent_unit_id = subtree.id
        )
        SELECT DISTINCT id FROM subtree;
    """
    with connection.cursor() as cursor:
        # We use .hex because SQLite stores UUIDs as char(32) without dashes
        # Postgres accepts UUIDs without dashes as well.
        cursor.execute(sql, [user.pk.hex])
        rows = cursor.fetchall()
        
    ids = [str(row[0]) for row in rows]
    return OrgUnit.objects.filter(id__in=ids)
