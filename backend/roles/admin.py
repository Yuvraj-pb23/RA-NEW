from django.contrib import admin
from .models import Role, RolePermission


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0
    fields = ["permission_key", "permission_value"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = [
        "role_name", "organization", "is_supervisor_role", "hierarchy_level",
        "parent_role", "has_supervisor_visibility", "status", "created_at",
    ]
    list_filter = ["status", "organization", "is_supervisor_role", "has_supervisor_visibility"]
    search_fields = ["role_name", "organization__name"]
    ordering = ["organization", "is_supervisor_role", "hierarchy_level"]
    inlines = [RolePermissionInline]
    raw_id_fields = ["parent_role", "created_by"]


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ["role", "permission_key", "permission_value"]
    list_filter = ["permission_key", "permission_value"]
