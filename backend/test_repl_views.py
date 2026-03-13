import re
with open("orgs/views.py", "r") as f:
    text = f.read()

old_query = """        return Organization.objects.annotate(
            unit_count=Count("org_units", distinct=True),
            project_count=Count("org_units__projects", distinct=True),
        )"""

new_query = """        return Organization.objects.annotate(
            unit_count=Count("org_units", distinct=True),
            project_count=Count("org_units__org_unit_projects", distinct=True),
            road_count=Count("org_units__org_unit_projects__roads", distinct=True),
        )"""

text = text.replace(old_query, new_query)
with open("orgs/views.py", "w") as f:
    f.write(text)
