from django.contrib import admin

from .models import *


class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type']
    
class PostAdmin(admin.ModelAdmin):
    list_display = ['event', 'file_type', 'group']
    

class CustomerPostFrameMappingAdmin(admin.ModelAdmin):
    list_display = ['customer', 'post']

admin.site.register(Category)
admin.site.register(Event, EventAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(OtherPost)
admin.site.register(CustomerPostFrameMapping, CustomerPostFrameMappingAdmin)
admin.site.register(CustomerOtherPostFrameMapping)
admin.site.register(BusinessPost)
admin.site.register(BusinessPostFrameMapping)


                    
