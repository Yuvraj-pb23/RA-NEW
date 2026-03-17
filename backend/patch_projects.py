import re

with open('templates/dashboard/projects/list.html', 'r') as f:
    content = f.read()

# I want to add {% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER' %} around the edit & delete buttons
old_str = """                <td class="table-td">
                  <div class="flex items-center justify-end gap-1.5">
                    <button @click="openEdit"""

new_str = """                <td class="table-td">
                  <div class="flex items-center justify-end gap-1.5">
                    {% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER' %}
                    <button @click="openEdit"""

if old_str in content:
    content = content.replace(old_str, new_str)
    
old_str2 = """                    </button>
                  </div>
                </td>"""

new_str2 = """                    </button>
                    {% endif %}
                  </div>
                </td>"""

if old_str2 in content:
    content = content.replace(old_str2, new_str2)

with open('templates/dashboard/projects/list.html', 'w') as f:
    f.write(content)
print("done")
