import re

with open("orgs/views.py", "r") as f:
    text = f.read()

# remove extra imports
text = re.sub(r'(from core\.permissions import IsSuperAdminOrReadOnly\n)+', 'from core.permissions import IsSuperAdminOrReadOnly\n', text)

with open("orgs/views.py", "w") as f:
    f.write(text)
