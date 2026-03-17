with open('templates/layouts/base.html', 'r') as f:
    text = f.read()

import re

# We need to change the sidebar permissions.
# Dashboard is everyone
# Organizations is SUPER_ADMIN
# Hierarchy is SUPER_ADMIN, ORG_ADMIN
# Org Units is SUPER_ADMIN, ORG_ADMIN
# Projects is everyone
# Roads is everyone
# Access / Users is SUPER_ADMIN, ORG_ADMIN

# Here is the text patching.

# 1. ORG UNITS:
# BEFORE: {% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER' %}
# AFTER: {% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN' %}
# Wait, actually let's just make it simple: SUPER_ADMIN and ORG_ADMIN
text = re.sub(
    r"{%\s*if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER'\s*%}",
    "{% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN' %}",
    text
)

# 2. PROJECTS:
# BEFORE: {% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER,PIU_USER' %}
# AFTER: Everyone can view so let's remove the condition for projects... Wait, let's just keep it as `SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER,PIU_USER,PROJECT_USER` essentially meaning all, or remove the wrap.
# Let's remove the wrap for Projects because ALL end users see projects.
# Actually I'll just change the string to include PROJECT_USER.
text = re.sub(
    r"{%\s*if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER,PIU_USER'\s*%}",
    "{% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER,PIU_USER,PROJECT_USER' %}",
    text
)

# Wait... Users was originally: `{% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER,RO_USER,PIU_USER' %}`
# So if it was that, we just globally replaced it. That means Users will be shown to everyone too. 
# We need to be careful!
