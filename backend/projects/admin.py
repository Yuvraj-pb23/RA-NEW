from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display   = ["name", "organization", "org_unit", "created_at"]
    list_filter    = ["organization"]
    search_fields  = ["name", "description"]
    raw_id_fields  = ["organization", "org_unit"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = [
        (None, {
            "fields": ["id", "name", "organization", "org_unit", "description"],
        }),
        ("Timestamps", {
            "fields": ["created_at", "updated_at"],
            "classes": ["collapse"],
        }),
    ]
