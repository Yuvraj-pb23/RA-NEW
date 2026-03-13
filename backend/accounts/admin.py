from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Extends Django's built-in UserAdmin to work with our email-based User model.
    """

    ordering      = ("email",)
    search_fields = ("email", "full_name", "phone")
    list_display  = ("email", "full_name", "is_active", "is_staff", "date_joined")
    list_filter   = ("is_active", "is_staff", "is_superuser")
    readonly_fields = ("id", "date_joined", "updated_at", "last_login")

    # Override fieldsets — replace username with email
    fieldsets = (
        (None, {
            "fields": ("id", "email", "password"),
        }),
        (_("Personal info"), {
            "fields": ("full_name", "phone"),
        }),
        (_("Permissions"), {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
            "classes": ("collapse",),
        }),
        (_("Important dates"), {
            "fields": ("last_login", "date_joined", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # Fields shown on the "Add User" page
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2"),
        }),
    )
