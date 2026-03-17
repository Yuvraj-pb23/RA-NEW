with open('templates/dashboard/roads/list.html', 'r') as f:
    content = f.read()

content = content.replace("this._fetchProjects();", "this._fetchProjects();\n      setTimeout(initMap, 500);")
with open('templates/dashboard/roads/list.html', 'w') as f:
    f.write(content)
