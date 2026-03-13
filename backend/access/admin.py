from django.contrib import admin

from .models import UserOrgAccess


class UserOrgAccessInline(admin.TabularInline):
    model = UserOrgAccess
    extra = 0
    fields = ("org_unit", "role", "is_active", "assigned_by")
    readonly_fields = ("created_at",)
    raw_id_fields = ("org_unit", "assigned_by")


@admin.register(UserOrgAccess)
class UserOrgAccessAdmin(admin.ModelAdmin):
    list_display  = (
        "user", "org_unit_name", "org_name", "role", "is_active", "created_at"
    )
    list_filter   = ("role", "is_active", "org_unit__organization")
    search_fields = ("user__email", "org_unit__name", "org_unit__organization__name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("user", "org_unit", "assigned_by")
    fieldsets = (
        (None, {
            "fields": ("id", "user", "org_unit", "role", "is_active"),
        }),
        ("Audit", {
            "fields": ("assigned_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def org_unit_name(self, obj):
        return obj.org_unit.name
    org_unit_name.short_description = "Org Unit"
    org_unit_name.admin_order_field = "org_unit__name"

    def org_name(self, obj):
        return obj.org_unit.organization.name
    org_name.short_description = "Organization"
    org_name.admin_order_field = "org_unit__organization__name"
