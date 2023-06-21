from django.db import models

from lib.models import BaseModel
from account.models import User


class Banner(BaseModel):
    image = models.FileField(upload_to="banner/", null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class BirthdayPost(BaseModel):
    image = models.FileField(upload_to="birthday_post/", null=True, blank=True)


class SplashScreen(BaseModel):
    file = models.FileField(upload_to="splash_screen/", null=True, blank=True)


class Tutorials(BaseModel):
    name = models.CharField(max_length=100, null=True, blank=True)
    url = models.URLField(null=True, blank=True)


class About(BaseModel):
    address = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    whatsapp_number = models.CharField(max_length=100, null=True, blank=True)
    website = models.CharField(max_length=50, null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    instagram = models.URLField(null=True, blank=True)
    youtube = models.URLField(null=True, blank=True)


class PrivacyPolicy(BaseModel):
    data = models.TextField(null=True, blank=True)


class TermsAndCondition(BaseModel):
    data = models.TextField(null=True, blank=True)


class Feedback(BaseModel):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    feedback = models.TextField()
    
    def __str__(self) -> str:
        return self.customer.whatsapp_number
    






