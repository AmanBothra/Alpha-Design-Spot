from django.contrib import admin

from .models import *

admin.site.register(Category)
admin.site.register(Event)
admin.site.register(Post)
admin.site.register(OtherPost)
admin.site.register(CustomerPostFrameMapping)
admin.site.register(CustomerOtherPostFrameMapping)
                    
