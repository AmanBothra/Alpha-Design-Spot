from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime

from .models import CustomerFrame
from app_modules.post.models import (
    Event, Post, OtherPost, CustomerPostFrameMapping, CustomerOtherPostFrameMapping, BusinessPost,
    BusinessPostFrameMapping
)

@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_posts(sender, instance, created, **kwargs):
    if not created:
        customer = instance.customer
        customer_group = instance.group

        current_date = datetime.date.today()
        future_events = Event.objects.filter(event_date__gte=current_date)

        posts = Post.objects.select_related('event', 'group').filter(
            group=customer_group, event__in=future_events
        )
        
        # Retrieve existing CustomerPostFrameMapping instances
        existing_mappings = CustomerPostFrameMapping.objects.filter(
            customer=customer,
            post__group=customer_group
        )
        
        for post in posts:
            # Update existing mappings or create new ones
            mapping, created = CustomerPostFrameMapping.objects.get_or_create(
                customer=customer,
                post=post,
                defaults={'customer_frame': instance}
            )

            if not created:
                mapping.customer_frame = instance
                mapping.save()
            
            # Mark existing mappings as downloaded if needed
            if mapping.is_downloaded:
                mapping.is_downloaded = False
                mapping.save()

                
                


@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_other_posts(sender, instance, created, **kwargs):
    if not created:  # Only update existing records, ignore new creations
        customer = instance.customer
        customer_group = instance.group

        other_posts = OtherPost.objects.filter(
            group=customer_group,
        ).select_related('group', 'category')
        
        for other_post in other_posts:
            mapping, created = CustomerOtherPostFrameMapping.objects.get_or_create(
                customer=customer,
                other_post=other_post,
                defaults={'customer_frame': instance}
            )

            if not created:
                mapping.customer_frame = instance
                mapping.save()


@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_business_posts(sender, instance, created, **kwargs):
    if not created: 
        customer = instance.customer
        customer_group = instance.group
        category = instance.business_category
        sub_category = instance.business_sub_category
        
        business_posts = BusinessPost.objects.filter(
            business_category=category, business_sub_category=sub_category
        ).select_related('business_category', 'business_sub_category')

        for business_post in business_posts:
            mapping, created = BusinessPostFrameMapping.objects.get_or_create(
                customer=customer,
                post=business_post,
                defaults={'customer_frame': instance}
            )

            if not created:
                mapping.customer_frame = instance
                mapping.save()
