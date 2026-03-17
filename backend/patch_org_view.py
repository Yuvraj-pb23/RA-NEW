import re
with open('orgs/views.py', 'r') as f:
    text = f.read()

text = text.replace('from access.permissions import IsAdminOrReadOnly', 'from access.permissions import IsAdminOrReadOnly\nfrom core.permissions import IsSuperAdminOrReadOnly')
text = re.sub(
    r'class OrganizationViewSet\(viewsets\.ModelViewSet\):.*?permission_classes = \[IsAuthenticated, IsAdminOrReadOnly\]',
    'class OrganizationViewSet(viewsets.ModelViewSet):\n    """\n    CRUD for organizations.\n    """\n    queryset = Organization.objects.all()\n    serializer_class = OrganizationSerializer\n    permission_classes = [IsAuthenticated, IsSuperAdminOrReadOnly]',
    text,
    flags=re.DOTALL
)

with open('orgs/views.py', 'w') as f:
    f.write(text)
