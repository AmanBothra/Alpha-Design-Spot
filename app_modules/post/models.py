from django.db import models

from lib.models import BaseModel
from account.models import User, CustomerFrame
from lib.constants import FILE_TYPE


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    sub_category = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    banner_image = models.ImageField(upload_to='category_banners/', null=True, blank=True)
    
    def __str__(self) -> str:
        return self.name


class Event(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    event_date = models.DateField(null=True, blank=True)
    
    def __str__(self) -> str:
        return self.name


class Post(BaseModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="post_event")
    file_type = models.CharField(max_length=50, choices=FILE_TYPE, default='image')
    file = models.FileField(upload_to='post/')
    is_active = models.BooleanField(default=True)
    
    def __str__(self) -> str:
        return self.event.name


class OtherPost(BaseModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="other_post_categories")
    name = models.CharField(max_length=100)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE, default='image')
    file = models.FileField(upload_to='other_post/')
    is_active = models.BooleanField(default=True)


class DownloadPost(BaseModel):
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="customer_download_post"
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="download_post"
    )
    other_post = models.ForeignKey(
        OtherPost,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="download_other_post"
    )


class CustomerPostFrameMapping(BaseModel):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="frame_mapping")
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="post_mapping"
    )
    customer_frame = models.ForeignKey(
        CustomerFrame,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="customer_frame_mapping"
    )
    is_downloaded = models.BooleanField(default=False)

