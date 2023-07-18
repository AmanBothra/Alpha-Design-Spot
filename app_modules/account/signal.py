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
    
    with transaction.atomic():
        for post in posts:
            mapping, _ = CustomerPostFrameMapping.objects.get_or_create(
                customer=customer,
                post=post,
                customer_frame=instance
            )
            mapping.is_downloaded = False
            mapping.save()
        
        
@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_other_posts(sender, instance, created, **kwargs):
    customer = instance.customer
    customer_group = instance.group

    other_posts = OtherPost.objects.filter(
        group=customer_group,
    ).select_related('group', 'category')
    
    with transaction.atomic():
        for other_post in other_posts:
            mapping, _ = CustomerOtherPostFrameMapping.objects.get_or_create(
                customer=customer,
                other_post=other_post,
                customer_frame=instance
            )
            mapping.is_downloaded = False
            mapping.save()
