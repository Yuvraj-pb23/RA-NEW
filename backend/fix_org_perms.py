with open("orgs/views.py", "r") as f:
    text = f.read()

text = text.replace("from core.permissions import IsOrgAdminOrReadOnly", "from core.permissions import IsOrgAdminOrReadOnly, IsSuperAdminOrReadOnly")

# We want only OrganizationViewSet to use IsSuperAdminOrReadOnly.
# It currently has: permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
# Let's string replace the specific occurrence for OrganizationViewSet.

old_block = """    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]"""

new_block = """    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrReadOnly]"""

text = text.replace(old_block, new_block)

with open("orgs/views.py", "w") as f:
    f.write(text)
