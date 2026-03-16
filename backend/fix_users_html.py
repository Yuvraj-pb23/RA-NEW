with open("templates/dashboard/users/list.html", "r") as f:
    html = f.read()

# Fix duplicated table headers
old_th = """            <th class="table-th">User</th>
            <th class="table-th hidden sm:table-cell">Email</th>
            <th class="table-th">Role</th>
            <th class="table-th hidden sm:table-cell">Assigned Unit</th>
            <th class="table-th">Role</th>
            <th class="table-th hidden sm:table-cell">Assigned Unit</th>
            <th class="table-th">Status</th>"""
            
new_th = """            <th class="table-th">User</th>
            <th class="table-th hidden sm:table-cell">Email</th>
            <th class="table-th">Role</th>
            <th class="table-th hidden sm:table-cell">Assigned Unit</th>
            <th class="table-th">Status</th>"""
html = html.replace(old_th, new_th)

# Fix duplicated table cols
old_td = """                <td class="table-td hidden sm:table-cell text-slate-500" x-text="user.email"></td>
                <td class="table-td">
                  <span class="text-xs text-slate-600" x-text="user.role.replace('_', ' ')"></span>
                </td>
                <td class="table-td hidden sm:table-cell">
                  <span class="text-xs text-slate-500" x-text="user.assigned_unit ? user.assigned_unit.name : '—'"></span>
                </td>
                <td class="table-td">
                  <span class="text-xs text-slate-600" x-text="user.role.replace('_', ' ')"></span>
                </td>
                <td class="table-td hidden sm:table-cell">
                  <span class="text-xs text-slate-500" x-text="user.assigned_unit ? user.assigned_unit.name : '—'"></span>
                </td>
                <td class="table-td">
                  <span :class="user.is_active ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'\""""

new_td = """                <td class="table-td hidden sm:table-cell text-slate-500" x-text="user.email"></td>
                <td class="table-td">
                  <span class="text-xs text-slate-600" x-text="(user.role || '').replace('_', ' ')"></span>
                </td>
                <td class="table-td hidden sm:table-cell">
                  <span class="text-xs text-slate-500" x-text="user.assigned_unit ? user.assigned_unit.name : '—'"></span>
                </td>
                <td class="table-td">
                  <span :class="user.is_active ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'\""""
                  
html = html.replace(old_td, new_td)

with open("templates/dashboard/users/list.html", "w") as f:
    f.write(html)
