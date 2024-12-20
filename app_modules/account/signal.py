import datetime
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import *

from app_modules.post.models import *
from .models import CustomerFrame


@receiver(post_save, sender=CustomerFrame)
def trigger_mapping_post_task(sender, instance, created, **kwargs):
    if created:
        # mapping_customer_frame_with_post.delay(instance.id)
        mapping_customer_frame_with_post(instance.id)


@receiver(post_save, sender=CustomerFrame)
def trigger_mapping_task(sender, instance, created, **kwargs):
    if created:
        # mapping_customer_frame_with_other_posts.delay(instance.id)
        mapping_customer_frame_with_other_posts(instance.id)


@receiver(post_save, sender=CustomerFrame)
def trigger_customer_frame_mapping(sender, instance, created, **kwargs):
    if created:
        # map_customer_frame_with_business_posts.delay(instance.id)
        map_customer_frame_with_business_posts(instance.id)
