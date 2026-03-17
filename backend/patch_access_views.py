import re

with open("access/views.py", "r") as f:
    text = f.read()

text = text.replace("permission_classes = [IsAuthenticated]", "permission_classes = [IsAuthenticated, IsAdminOrReadOnly]")
if "IsAdminOrReadOnly" not in text:
    text = text.replace("from rest_framework.permissions import IsAuthenticated", "from rest_framework.permissions import IsAuthenticated\nfrom .permissions import IsAdminOrReadOnly")

with open("access/views.py", "w") as f:
    f.write(text)
print("Done access views")
