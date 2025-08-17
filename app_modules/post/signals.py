from django.db.models.signals import post_save
from django.dispatch import receiver

from app_modules.post.tasks import (
    map_post_with_customer_frames,
    map_other_post_with_customer_frames,
    map_business_post_with_customer_frames,
)
from .models import Post, OtherPost, BusinessPost


@receiver(post_save, sender=Post)
def trigger_post_mapping(sender, instance, created, **kwargs):
    """Trigger post mapping when a new Post is created."""
    if created:
        map_post_with_customer_frames(instance.id)


@receiver(post_save, sender=OtherPost)
def trigger_other_post_mapping(sender, instance, created, **kwargs):
    """Trigger other post mapping when a new OtherPost is created."""
    if created:
        map_other_post_with_customer_frames(instance.id)


@receiver(post_save, sender=BusinessPost)
def trigger_business_post_mapping(sender, instance, created, **kwargs):
    """Trigger business post mapping when a new BusinessPost is created."""
    if created:
        map_business_post_with_customer_frames(instance.id)
