import re

with open('templates/dashboard/users/list.html', 'r') as f:
    content = f.read()

old_select = """<select x-model="form.role" @change="onRoleChange()" class="input-base">
            <option value="SUPER_ADMIN">Super Admin</option>
            <option value="ORG_ADMIN">Org Admin</option>
            <option value="HO_USER">HO User</option>
            <option value="RO_USER">RO User</option>
            <option value="PIU_USER">PIU User</option>
            <option value="PROJECT_USER">Project User</option>
          </select>"""

new_select = """<select x-model="form.role" @change="onRoleChange()" class="input-base">
            {% if request.user.role == 'SUPER_ADMIN' %}
            <option value="ORG_ADMIN">Org Admin</option>
            <option value="HO_USER">HO User</option>
            <option value="RO_USER">RO User</option>
            <option value="PIU_USER">PIU User</option>
            <option value="PROJECT_USER">Project User</option>
            {% elif request.user.role == 'ORG_ADMIN' %}
            <option value="HO_USER">HO User</option>
            <option value="RO_USER">RO User</option>
            <option value="PIU_USER">PIU User</option>
            <option value="PROJECT_USER">Project User</option>
            {% elif request.user.role == 'HO_USER' %}
            <option value="RO_USER">RO User</option>
            <option value="PIU_USER">PIU User</option>
            <option value="PROJECT_USER">Project User</option>
            {% elif request.user.role == 'RO_USER' %}
            <option value="PIU_USER">PIU User</option>
            <option value="PROJECT_USER">Project User</option>
            {% elif request.user.role == 'PIU_USER' %}
            <option value="PROJECT_USER">Project User</option>
            {% endif %}
          </select>"""

if old_select in content:
    content = content.replace(old_select, new_select)
    with open('templates/dashboard/users/list.html', 'w') as f:
        f.write(content)
    print("Patched select successfully!")
else:
    print("Could not find the target string!")

