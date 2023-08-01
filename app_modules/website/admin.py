from django.contrib import admin

from app_modules.website import models


admin.site.register(models.Testimonial)
admin.site.register(models.Enquiry)
