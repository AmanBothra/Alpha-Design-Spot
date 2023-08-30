from django.contrib import admin

from app_modules.master.models import (
    Banner, BirthdayPost, SplashScreen, Tutorials, About, PrivacyPolicy, TermsAndCondition, Feedback,
)

admin.site.register(BirthdayPost)
admin.site.register(Banner)
admin.site.register(SplashScreen)
admin.site.register(Tutorials)
admin.site.register(About)
admin.site.register(PrivacyPolicy)
admin.site.register(TermsAndCondition)
admin.site.register(Feedback)

