from django.contrib.auth.models import AbstractUser
from django.db import models

from lib.constants import USER_TYPE
from .managers import UserManager


class User(AbstractUser):
    user_type = models.CharField(max_length=100, choices=USER_TYPE)
    whatsapp_number = models.CharField(max_length=20, blank=True, unique=True)
    address = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    dob = models.DateField(null=True, blank=True)
    frame_img = models.ImageField(upload_to='frame_images/', blank=True)
    no_of_post = models.IntegerField(default=0)
    is_verify = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ['email']
    
    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}({self.whatsapp_number})"
    
    