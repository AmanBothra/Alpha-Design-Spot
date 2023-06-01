from django.db import models

from lib.models import BaseModel
from account.models import User
from lib.constants import FILE_TYPE


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    sub_category = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    banner_image = models.ImageField(upload_to='category_banners/', null=True, blank=True)


class Event(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    event_date = models.DateField(null=True, blank=True)


class Post(BaseModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE, default='image')
    file = models.FileField(upload_to='post/')
    is_active = models.BooleanField(default=True)


class OtherPost(BaseModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE, default='image')
    file = models.FileField(upload_to='other_post/')
    is_active = models.BooleanField(default=True)


class DownloadPost(BaseModel):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    other_post = models.ForeignKey(OtherPost, on_delete=models.CASCADE, null=True, blank=True)


class CustomerPostFrameMapping(BaseModel):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    is_downloaded = models.BooleanField(default=False)

