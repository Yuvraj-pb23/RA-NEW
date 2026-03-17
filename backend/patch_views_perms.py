import re

# orgs/views.py
with open("orgs/views.py", "r") as f:
    text = f.read()
text = re.sub(
    r"class OrgUnitViewSet\(viewsets\.ModelViewSet\):.*?permission_classes = \[IsAuthenticated\]",
    "class OrgUnitViewSet(viewsets.ModelViewSet):\n    \"\"\"\n    CRUD for org units.\n    \"\"\"\n    queryset = OrgUnit.objects.all().select_related('organization', 'level', 'parent')\n    serializer_class = OrgUnitSerializer\n    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]",
    text,
    flags=re.DOTALL
)
with open("orgs/views.py", "w") as f:
    f.write(text)

# projects/views.py
with open("projects/views.py", "r") as f:
    text = f.read()
if "permission_classes" not in text:
    text = text.replace("from rest_framework.viewsets import ModelViewSet\n", "from rest_framework.viewsets import ModelViewSet\nfrom rest_framework.permissions import IsAuthenticated\nfrom access.permissions import IsAdminOrReadOnly\n")
    text = text.replace("class ProjectViewSet(ModelViewSet):\n", "class ProjectViewSet(ModelViewSet):\n    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]\n")
with open("projects/views.py", "w") as f:
    f.write(text)

# roads/views.py
with open("roads/views.py", "r") as f:
    text = f.read()
if "permission_classes" not in text:
    text = text.replace("from rest_framework.viewsets import ModelViewSet\n", "from rest_framework.viewsets import ModelViewSet\nfrom rest_framework.permissions import IsAuthenticated\nfrom access.permissions import IsAdminOrReadOnly\n")
    text = text.replace("class RoadViewSet(ModelViewSet):\n", "class RoadViewSet(ModelViewSet):\n    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]\n")
with open("roads/views.py", "w") as f:
    f.write(text)

print("done")
