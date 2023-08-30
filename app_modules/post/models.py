from account.models import User, CustomerFrame, CustomerGroup
from django.db import models

from lib.constants import FILE_TYPE, PROFESSION_TYPE
from lib.helpers import rename_file_name, converter_to_webp
from lib.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    sub_category = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    banner_image = models.ImageField(upload_to='category_banners/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.banner_image:
            converter_to_webp(self.banner_image)
        super().save(*args, **kwargs)


class Event(BaseModel):
    name = models.CharField(max_length=100)
    event_date = models.DateField(null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=FILE_TYPE, default='image')
    thumbnail = models.FileField(upload_to=rename_file_name('event_thumbnail/'), null=True)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.thumbnail:
            converter_to_webp(self.thumbnail)
        super().save(*args, **kwargs)


class Post(BaseModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="post_event")
    file_type = models.CharField(max_length=50, choices=FILE_TYPE, default='image')
    file = models.FileField(upload_to=rename_file_name('post/'))
    group = models.ForeignKey(
        CustomerGroup,
        on_delete=models.CASCADE,
        related_name="customer_post_group",
        null=True, blank=True
    )

    def __str__(self) -> str:
        return self.event.name
    
    def save(self, *args, **kwargs):
        if self.file_type == 'image':
            converter_to_webp(self.file)
        super().save(*args, **kwargs)


class OtherPost(BaseModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="other_post_categories")
    name = models.CharField(max_length=100)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE, default='image')
    file = models.FileField(upload_to=rename_file_name('other_post/'))
    group = models.ForeignKey(
        CustomerGroup,
        on_delete=models.CASCADE,
        related_name="customer_other_post_group",
        null=True, blank=True
    )

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.file_type == "image":
            converter_to_webp(self.file)
        super().save(*args, **kwargs)
        
   
class BusinessCategory(BaseModel):
    profession_type = models.CharField(max_length=20, choices=PROFESSION_TYPE)
    name = models.CharField(max_length=100, unique=True)
    thumbnail = models.FileField(upload_to=rename_file_name('business_category_thumbnail/'))
    
    def __str__(self) -> str:
        return self.name
    
    
    def save(self, *args, **kwargs):
        if self.thumbnail:
            converter_to_webp(self.thumbnail)
        super().save(*args, **kwargs)   

     
class BusinessPost(BaseModel):
    profession_type = models.CharField(max_length=20, choices=PROFESSION_TYPE, null=True, blank=True)
    business_category = models.ForeignKey(
        BusinessCategory,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="business_sub_category_posts"
    )
    file_type = models.CharField(max_length=50, choices=FILE_TYPE, default='image')
    file = models.FileField(upload_to=rename_file_name('business_post/'))
    group = models.ForeignKey(
        CustomerGroup,
        on_delete=models.CASCADE,
        related_name="business_post_group",
        null=True, blank=True
    )

    def __str__(self) -> str:
        return f"Category is {self.business_category.name} and Profession is {self.profession_type}"


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

    def __str__(self) -> str:
        return self.customer.whatsapp_number


class CustomerOtherPostFrameMapping(BaseModel):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="other_post_frame_mapping")
    other_post = models.ForeignKey(
        OtherPost,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="other_post_mapping"
    )
    customer_frame = models.ForeignKey(
        CustomerFrame,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="customer_other_post_frame_mapping"
    )
    is_downloaded = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.customer.whatsapp_number


class BusinessPostFrameMapping(BaseModel):
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="business_post_frame_mapping"
    )
    post = models.ForeignKey(
        BusinessPost,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="business_post_mapping"
    )
    customer_frame = models.ForeignKey(
        CustomerFrame,
        on_delete=models.CASCADE,
        null=True, blank=True,
    )
    is_downloaded = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.customer.whatsapp_number