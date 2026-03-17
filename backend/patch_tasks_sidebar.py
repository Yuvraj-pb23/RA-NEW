with open('templates/layouts/base.html', 'r') as f:
    text = f.read()

tasks_html = """
      <a href="#" :title="col?'My Tasks':''"
         class="sidebar-link {% if ap == 'tasks' %}sidebar-link-active{% else %}sidebar-link-inactive{% endif %}">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        <span x-show="!col">My Tasks</span>
      </a>"""

if "My Tasks" not in text:
    text = text.replace('<span x-show="!col">Roads</span>\n      </a>', '<span x-show="!col">Roads</span>\n      </a>\n' + tasks_html)
    with open('templates/layouts/base.html', 'w') as f:
        f.write(text)
    print("Patched My Tasks in sidebar")
