from django.contrib.auth.models import AbstractUser
from django.db import models

from lib.constants import USER_TYPE
from lib.helpers import rename_file_name, get_image_file_extension_validator
from .managers import UserManager


class User(AbstractUser):
    username = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=100, choices=USER_TYPE)
    whatsapp_number = models.CharField(max_length=20, blank=True, unique=True)
    address = models.TextField(null=True, blank=True)
    pincode = models.IntegerField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    frame_img = models.ImageField(
        upload_to=rename_file_name('frame_images/'),
        validators=[get_image_file_extension_validator],
        blank=True
    )
    no_of_post = models.IntegerField(default=0)
    is_verify = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}({self.whatsapp_number})"
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        password = self.password
        if len(password) < 40:
            self.set_password(password)
        super(User, self).save(*args, **kwargs)