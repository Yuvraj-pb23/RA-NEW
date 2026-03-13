from django.contrib import admin

from .models import Organization, HierarchyLevel, OrgUnit


class HierarchyLevelInline(admin.TabularInline):
    model = HierarchyLevel
    extra = 1
    fields = ("level_name", "level_order", "parent_level")
    ordering = ("level_order",)


class OrgUnitInline(admin.TabularInline):
    model = OrgUnit
    extra = 0
    fields = ("name", "level", "parent_unit", "is_active")
    readonly_fields = ("created_at",)
    show_change_link = True


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display  = ("name", "country", "is_active", "created_at")
    list_filter   = ("country", "is_active")
    search_fields = ("name", "country")
    inlines       = [HierarchyLevelInline]
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("id", "name", "country", "description", "is_active"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(HierarchyLevel)
class HierarchyLevelAdmin(admin.ModelAdmin):
    list_display  = ("organization", "level_name", "level_order", "parent_level")
    list_filter   = ("organization",)
    search_fields = ("level_name", "organization__name")
    ordering      = ("organization", "level_order")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(OrgUnit)
class OrgUnitAdmin(admin.ModelAdmin):
    list_display  = ("name", "level_name", "organization", "parent_unit", "is_active")
    list_filter   = ("organization", "level", "is_active")
    search_fields = ("name", "organization__name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("parent_unit",)  # Avoid loading full dropdown for large trees
    fieldsets = (
        (None, {
            "fields": (
                "id", "organization", "name", "level",
                "parent_unit", "is_active",
            ),
        }),
        ("Extra Data", {
            "fields": ("metadata",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def level_name(self, obj):
        return obj.level.level_name
    level_name.short_description = "Level"
    level_name.admin_order_field = "level__level_order"
