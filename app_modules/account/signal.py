from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
from django.db import transaction

from .models import CustomerFrame
from app_modules.post.models import Event, Post, OtherPost, CustomerPostFrameMapping, CustomerOtherPostFrameMapping


@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_posts(sender, instance, created, **kwargs):
    customer = instance.customer
    customer_group = instance.group

    current_date = datetime.date.today()
    future_events = Event.objects.filter(event_date__gte=current_date)

    posts = Post.objects.select_related('event', 'group').filter(
        group=customer_group, event__in=future_events
    )
    
    mappings = [
        CustomerPostFrameMapping(
            customer=customer,
            post=post,
            customer_frame=instance,
            is_downloaded=False
        )
        for post in posts
    ]

    with transaction.atomic():
        CustomerPostFrameMapping.objects.bulk_create(mappings)
        
        
@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_oher_posts(sender, instance, created, **kwargs):
    customer = instance.customer
    customer_group = instance.group

    other_posts = OtherPost.objects.filter(
        group=customer_group,
    ).select_related('group', 'category')
    
    mappings = [
        CustomerOtherPostFrameMapping(
            customer=customer,
            other_post=other_post,
            customer_frame=instance,
            is_downloaded=False
        )
        for other_post in other_posts
    ]
    
    with transaction.atomic():
        print("signal call")
        CustomerOtherPostFrameMapping.objects.bulk_create(mappings)