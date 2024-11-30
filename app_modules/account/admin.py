from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from . import models
# Register your models here.
@admin.register(models.User)
class UserAdmin(DefaultUserAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "email",
        "whatsapp_number",
        "is_verify",
        "date_joined",
    )
    list_filter = ("date_joined",)
    search_fields = (
        "email",
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
                    "is_deleted",
                    "deleted_at",
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
                    "whatsapp_number",
                    "user_type",
                    "no_of_post",
                    "address",
                    "city",
                    "pincode",
                    "dob",
                    "is_verify"
                ),
            },
        ),
    )
    ordering = ("id",)
    
    

class CustomerFrameAdmin(admin.ModelAdmin):
    list_display = ['customer', 'group']
    
    
admin.site.register(models.CustomerFrame, CustomerFrameAdmin)
admin.site.register(models.CustomerGroup)
admin.site.register(models.Plan)
admin.site.register(models.Subscription)
admin.site.register(models.PaymentMethod)
admin.site.register(models.UserCode)
