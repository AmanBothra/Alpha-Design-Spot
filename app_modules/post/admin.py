from django.contrib import admin

from .models import *  # noqa: F403


class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type']


class PostAdmin(admin.ModelAdmin):
    list_display = ['event', 'file_type', 'group']


class CustomerPostFrameMappingAdmin(admin.ModelAdmin):
    list_display = ['customer', 'post', 'customer_frame']


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'sub_category']


admin.site.register(Category, CategoryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(OtherPost)
admin.site.register(CustomerPostFrameMapping, CustomerPostFrameMappingAdmin)
admin.site.register(CustomerOtherPostFrameMapping)
admin.site.register(BusinessPost)
admin.site.register(BusinessPostFrameMapping)
admin.site.register(BusinessCategory)
