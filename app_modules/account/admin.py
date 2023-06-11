from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from . import models
# Register your models here.
@admin.register(models.User)
class UserAdmin(DefaultUserAdmin):
    list_display = (
        "id",
        "email",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("date_joined",)
    search_fields = (
        "email",
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "whatsapp_number", "user_type", "no_of_post")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_superuser",
                    "is_staff",
                    "is_verify",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    ordering = ("id",)
    
    
admin.site.register(models.CustomerFrame)
admin.site.register(models.CustomerGroup)
admin.site.register(models.Plan)
admin.site.register(models.Subscription)
