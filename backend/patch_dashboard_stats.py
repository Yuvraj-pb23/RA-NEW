import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from api.v1.views import dashboard_stats
print(dashboard_stats)
