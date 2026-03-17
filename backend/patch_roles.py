import re

with open("accounts/models.py", "r") as f:
    text = f.read()

if "CONTRACTOR" not in text:
    text = text.replace(
        'PROJECT_USER = "PROJECT_USER", _("Project User")',
        'PROJECT_USER = "PROJECT_USER", _("Project User")\n    CONTRACTOR = "CONTRACTOR", _("Contractor")'
    )
    with open("accounts/models.py", "w") as f:
        f.write(text)
    print("Added CONTRACTOR role")
