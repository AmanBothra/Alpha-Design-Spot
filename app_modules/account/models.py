import random

from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError
from django.db import models
from django.utils import timezone

from lib.constants import USER_TYPE, UserConstants, PROFESSION_TYPE
from lib.helpers import rename_file_name, converter_to_webp
from lib.models import BaseModel
from .managers import UserManager


class User(AbstractUser, BaseModel):
    username = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=100, choices=USER_TYPE)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    address = models.TextField(null=True, blank=True)
    pincode = models.IntegerField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    no_of_post = models.IntegerField(default=1)
    is_verify = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()
    
    class Meta:
        indexes = [
            models.Index(fields=['user_type', 'is_deleted']),
            models.Index(fields=['email', 'is_deleted']),
            models.Index(fields=['is_verify', 'user_type']),
            models.Index(fields=['whatsapp_number']),
            models.Index(fields=['no_of_post', 'user_type']),
            models.Index(fields=['created', 'user_type']),
        ]
    
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def __str__(self):
        return f"{self.first_name}"

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        password = self.password
        if len(password) < 40:
            self.set_password(password)
        super(User, self).save(*args, **kwargs)

    def get_or_create_user_code(self, code_type=UserConstants.FORGOTTEN_PASSWORD):
        try:
            user_code, created = UserCode.objects.get_or_create(
                user=self, code_type=code_type,
                defaults={"code": random.randint(1000, 9999)}
            )
            if not created:
                user_code.code = random.randint(1000, 9999)
                user_code.save()

            return user_code, created
        except IntegrityError:  # Handle the case when unique constraint is violated
            return self.get_or_create_user_code(code_type)


class UserCode(models.Model):
    code = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code_type = models.CharField(
        max_length=30,
        choices=UserConstants.get_code_type_choices(),
        default=UserConstants.FORGOTTEN_PASSWORD,
    )
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (("user", "code_type"),)

    def __str__(self):
        return f"Code for {self.user} is {self.code}"


class CustomerGroup(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.name}"


class CustomerFrame(BaseModel):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customer_frame")
    profession_type = models.CharField(max_length=100, choices=PROFESSION_TYPE, null=True, blank=True)
    business_category = models.ForeignKey(
        "post.BusinessCategory",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="business_category_frames"
    )
    frame_img = models.ImageField(
        upload_to=rename_file_name('customer_frame/'),
        blank=True, null=True
    )
    group = models.ForeignKey(
        CustomerGroup,
        on_delete=models.CASCADE,
        related_name="customer_frame_group",
        null=True, blank=True
    )
    display_name = models.CharField(max_length=20, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['customer', 'group']),
            models.Index(fields=['customer', 'profession_type']),
            models.Index(fields=['customer', 'business_category']),
            models.Index(fields=['group', 'profession_type']),
            models.Index(fields=['display_name']),
        ]

    def __str__(self) -> str:
        return f"{self.customer.whatsapp_number} and {self.group}"

    def save(self, *args, **kwargs):
        if self.frame_img:
            converter_to_webp(self.frame_img)
        super().save(*args, **kwargs)

    def is_a_group(self):
        # Check if the group name starts with 'A'
        return self.group.name.startswith('A') if self.group else False


class PaymentMethod(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Plan(BaseModel):
    name = models.CharField(max_length=100)
    duration_in_months = models.IntegerField(default=0)
    price = models.IntegerField(default=0)

    def __str__(self):
        return self.name


def order_number():
    last_subscription = Subscription.objects.all().order_by('id').last()
    if not last_subscription:
        return 'ADS1001'

    order_no = last_subscription.order_number
    try:
        order_int = int(order_no[3:])
    except ValueError:
        return 'ADS1001'

    new_order_int = order_int + 1
    new_order_no = f'ADS{new_order_int:04}'
    return new_order_no


class Subscription(BaseModel):
    order_number = models.CharField(max_length=10, default=order_number, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscription_users")
    frame = models.ForeignKey(CustomerFrame, on_delete=models.SET_NULL,
                              related_name="subscription_frames", null=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="subscription_plans")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE,
                                       related_name='subscription_payment_methods')
    start_date = models.DateField()
    end_date = models.DateField()
    transaction_number = models.CharField(max_length=50, null=True, blank=True)
    file = models.FileField(upload_to=rename_file_name('subscription/'), null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'end_date']),
            models.Index(fields=['end_date', 'is_active']),
            models.Index(fields=['user', 'frame']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['order_number']),
        ]

    def __str__(self) -> str:
        return f"{self.order_number} {self.plan.name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = order_number()
        if self.file:
            converter_to_webp(self.file)
        super().save(*args, **kwargs)
