import re

with open('templates/layouts/base.html', 'r') as f:
    text = f.read()

# Make Org Units only super/org admin
text = text.replace(
    "{% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER' %}",
    "{% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN' %}"
)

# Make Projects everyone (remove the if statement completely around Projects)
project_pattern = r"{% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER,PIU_USER' %}\s*(<a href=\"{% url 'dashboard:projects' %}.*?</a>)\s*{% endif %}"
text = re.sub(project_pattern, r"\1", text, flags=re.DOTALL)

# Access group (Users, Access Control) should be only SUPER_ADMIN, ORG_ADMIN
# It currently has:
# {% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER,PIU_USER' %}
# Let's find it.
text = text.replace(
    "<!-- ── Access group ── -->\n        {% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER,PIU_USER' %}",
    "<!-- ── Access group ── -->\n        {% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN' %}"
)

with open('templates/layouts/base.html', 'w') as f:
    f.write(text)

