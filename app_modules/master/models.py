from django.db import models

from lib.helpers import rename_file_name, converter_to_webp
from lib.models import BaseModel


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
    customer = models.ForeignKey("account.User", on_delete=models.CASCADE, null=True, blank=True)
    feedback = models.TextField()
    
    def __str__(self) -> str:
        return self.customer.whatsapp_number
    

class BusinessCategory(BaseModel):
    name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    sub_category = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    thumbnail = models.FileField(upload_to=rename_file_name('business_category_thumbnail/'), null=True)
    
    def __str__(self) -> str:
        return self.name
    
    
    def save(self, *args, **kwargs):
        if self.thumbnail:
            converter_to_webp(self.thumbnail)
        super().save(*args, **kwargs)


