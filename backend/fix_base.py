import re

with open('templates/layouts/base.html', 'r', encoding='utf-8') as f:
    text = f.read()

NAV_START = '<nav class="flex-1 overflow-y-auto overflow-x-hidden py-3 px-2 space-y-0.5">'
NAV_END = '</nav>'

new_nav = '''<nav class="flex-1 overflow-y-auto overflow-x-hidden py-3 px-2 space-y-0.5">
      {% with ap=active_page %}

      <!-- Dashboard -->
      <a href="{% url 'dashboard:home' %}" :title="col?'Dashboard':''" class="sidebar-link {% if ap == 'home' %}sidebar-link-active{% else %}sidebar-link-inactive{% endif %}">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
        </svg>
        <span x-show="!col">Dashboard</span>
      </a>

      <!-- Organizations -->
      {% if request.user.role == 'SUPER_ADMIN' %}
      <div x-show="!col" x-cloak class="px-2.5 pt-4 pb-1.5">
          <p class="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Organization</p>
      </div>
      <a href="{% url 'dashboard:organizations' %}" :title="col?'Organizations':''" class="sidebar-link {% if ap == 'organizations' %}sidebar-link-active{% else %}sidebar-link-inactive{% endif %}">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
        </svg>
        <span x-show="!col">Organizations</span>
      </a>
      {% endif %}

      {% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER' %}
      {% if request.user.role != 'SUPER_ADMIN' %}
      <div x-show="!col" x-cloak class="px-2.5 pt-4 pb-1.5">
          <p class="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Internal Management</p>
      </div>
      {% endif %}
      <a href="{% url 'dashboard:hierarchy' %}" :title="col?'Hierarchy':''" class="sidebar-link {% if ap == 'hierarchy' %}sidebar-link-active{% else %}sidebar-link-inactive{% endif %}">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"/>
        </svg>
        <span x-show="!col">Hierarchy</span>
      </a>
      <a href="{% url 'dashboard:org_units' %}" :title="col?'Org Units':''" class="sidebar-link {% if ap == 'org_units' %}sidebar-link-active{% else %}sidebar-link-inactive{% endif %}">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0zM15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
        <span x-show="!col">Org Units</span>
      </a>
      {% endif %}

      <!-- Roads group -->
      <div x-show="!col" x-cloak class="px-2.5 pt-4 pb-1.5">
        <p class="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Roads & Projects</p>
      </div>

      <a href="{% url 'dashboard:projects' %}" :title="col?'Projects':''" class="sidebar-link {% if ap == 'projects' %}sidebar-link-active{% else %}sidebar-link-inactive{% endif %}">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
        </svg>
        <span x-show="!col">Projects</span>
      </a>
      <a href="{% url 'dashboard:roads' %}" :title="col?'Roads':''" class="sidebar-link {% if ap == 'roads' %}sidebar-link-active{% else %}sidebar-link-inactive{% endif %}">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20H5a2 2 0 01-2-2V6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M9 20l2-2m-2 2l2 2m6-11v9m-3-3l3 3 3-3"/>
        </svg>
        <span x-show="!col">Roads</span>
      </a>

      {% if request.user.role not in 'SUPER_ADMIN,ORG_ADMIN,HO_USER' %}
      <a href="#" :title="col?'My Work':''" class="sidebar-link sidebar-link-inactive">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
        <span x-show="!col">My Work</span>
      </a>
      {% endif %}

      <!-- Access group -->
      {% if request.user.role in 'SUPER_ADMIN,ORG_ADMIN,HO_USER' %}
      <div x-show="!col" x-cloak class="px-2.5 pt-4 pb-1.5">
        <p class="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Access</p>
      </div>

      <a href="{% url 'dashboard:users' %}" :title="col?'Users':''" class="sidebar-link {% if ap == 'users' %}sidebar-link-active{% else %}sidebar-link-inactive{% endif %}">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
        </svg>
        <span x-show="!col">Users</span>
      </a>

      <a href="{% url 'dashboard:access' %}" :title="col? (request.user.role == 'SUPER_ADMIN' and 'Access Control' or 'Assignments') :''" class="sidebar-link {% if ap == 'access' %}sidebar-link-active{% else %}sidebar-link-inactive{% endif %}">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
        </svg>
        <span x-show="!col">{% if request.user.role == 'SUPER_ADMIN' %}Access Control{% else %}Assignments{% endif %}</span>
      </a>
      {% endif %}
      {% endwith %}
    </nav>'''

import sys
start = text.find(NAV_START)
end = text.find(NAV_END, start)
if start != -1 and end != -1:
    with open('templates/layouts/base.html', 'w', encoding='utf-8') as f:
        f.write(text[:start] + new_nav + text[end+len(NAV_END):])
else:
    print("Could not find nav tags")
    sys.exit(1)
