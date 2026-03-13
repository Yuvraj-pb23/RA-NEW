from django.contrib import admin

from .models import Road


@admin.register(Road)
class RoadAdmin(admin.ModelAdmin):
    list_display    = ["name", "project", "road_type", "length", "has_geometry_display", "created_at"]
    list_filter     = ["road_type", "project__organization"]
    search_fields   = ["name", "project__name", "project__organization__name"]
    raw_id_fields   = ["project"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = [
        (None, {
            "fields": ["id", "name", "project", "road_type", "length"],
        }),
        ("Geometry", {
            "fields": ["geometry"],
            "classes": ["collapse"],
        }),
        ("Timestamps", {
            "fields": ["created_at", "updated_at"],
            "classes": ["collapse"],
        }),
    ]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("project__organization")
        )

    @admin.display(boolean=True, description="Has Map")
    def has_geometry_display(self, obj):
        return obj.geometry is not None
