import re
with open("orgs/serializers.py", "r") as f:
    text = f.read()

text = text.replace('project_count = serializers.IntegerField(read_only=True)', 'project_count = serializers.IntegerField(read_only=True)\n    road_count    = serializers.IntegerField(read_only=True)')
text = text.replace('"project_count",', '"project_count",\n            "road_count",')

with open("orgs/serializers.py", "w") as f:
    f.write(text)
