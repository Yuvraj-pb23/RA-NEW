import re

with open('dashboard/views.py', 'r') as f:
    text = f.read()

text = text.replace(
    'if user_role in [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN, SystemRole.HO_USER, SystemRole.RO_USER]:',
    'if user_role in [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]:'
)
text = text.replace(
    'if user_role in [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN, SystemRole.HO_USER, SystemRole.RO_USER, SystemRole.PIU_USER]:',
    '# All users can see projects/roads\n        if True:'
)
# Projects should ideally always be shown since we want end users to view them too. Wait! the user says End Users show sidebar: Dashboard, Projects, Roads.
# So Projects and Roads card should just append for all.
# I just replaced it with `if True:` for the first instance.

# Let's fix the Users one to be only Super & Org admin:
text = text.replace(
    '# All users can see projects/roads\n        if True:\n            cards.append({\n                "label": "Users",',
    'if user_role in [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]:\n            cards.append({\n                "label": "Users",'
)
# That's messy. Let's do it cleanly by re-writing context generation:

new_method = """    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user_role = getattr(self.request.user, 'role', None)
        
        cards = []
        if user_role == SystemRole.SUPER_ADMIN:
            cards.append({
                "label": "Organizations",
                "url":   "/api/v1/organizations/",
                "link":  "/dashboard/organizations/",
                "bg":    "bg-indigo-100",
                "text":  "text-indigo-600",
                "icon":  '<svg class="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>',
            })
            
        if user_role in [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]:
            cards.append({
                "label": "Org Units",
                "url":   "/api/v1/org-units/",
                "link":  "/dashboard/org-units/",
                "bg":    "bg-violet-100",
                "text":  "text-violet-600",
                "icon":  '<svg class="w-5 h-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
            })
            
        cards.append({
            "label": "Projects",
            "url":   "/api/v1/projects/",
            "link":  "/dashboard/projects/",
            "bg":    "bg-blue-100",
            "text":  "text-blue-600",
            "icon":  '<svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>',
        })

        cards.append({
            "label": "Roads",
            "url":   "/api/v1/roads/",
            "link":  "/dashboard/roads/",
            "bg":    "bg-teal-100",
            "text":  "text-teal-600",
            "icon":  '<svg class="w-5 h-5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20H5a2 2 0 01-2-2V6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M9 20l2-2m-2 2l2 2m6-11v9m-3-3l3 3 3-3"/></svg>',
        })
        
        if user_role in [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]:
            cards.append({
                "label": "Users",
                "url":   "/api/v1/users/",
                "link":  "/dashboard/users/",
                "bg":    "bg-amber-100",
                "text":  "text-amber-600",
                "icon":  '<svg class="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>',
            })
            
        if user_role in [SystemRole.SUPER_ADMIN, SystemRole.ORG_ADMIN]:
            cards.append({
                "label": "Access Grants",
                "url":   "/api/v1/user-access/",
                "link":  "/dashboard/access/",
                "bg":    "bg-rose-100",
                "text":  "text-rose-600",
                "icon":  '<svg class="w-5 h-5 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>',
            })

        ctx["stat_cards"] = cards
        return ctx"""

context_pattern = re.compile(r"def get_context_data\(self, \*\*kwargs\):.*?return ctx", re.DOTALL)
text = context_pattern.sub(new_method, text)

with open('dashboard/views.py', 'w') as f:
    f.write(text)

