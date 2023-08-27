from django.db.models.signals import post_save, pre_save, Signal
from django.dispatch import receiver
import datetime

from .models import CustomerFrame
from app_modules.post.models import (
    Event, Post, OtherPost, CustomerPostFrameMapping, CustomerOtherPostFrameMapping, BusinessPost,
    BusinessPostFrameMapping
)
        
# @receiver(post_save, sender=CustomerFrame)
# def update_customer_frame_data(sender, instance, created, **kwargs):
#     if not created:  # Only perform this on updates, not on new creations
#         current_date = datetime.date.today()
#         future_events = Event.objects.filter(event_date__gte=current_date)
        
#         existing_posts = Post.objects.select_related('event', 'group').filter(
#             group=instance.group, event__in=future_events
#         )
        
#         for post in existing_posts:
#             mapping = CustomerPostFrameMapping.objects.filter(
#                 customer_frame=instance,
#                 post=post
#             ).first()

#             if mapping:
#                 # Update existing mapping
#                 mapping.customer_frame = instance
#                 if mapping.is_downloaded:
#                     mapping.is_downloaded = False
#                 mapping.save()
#             else:
#                 # Create new mapping
#                 new_mapping = CustomerPostFrameMapping.objects.create(
#                     customer=instance.customer,
#                     post=post,
#                     customer_frame=instance,
#                     is_downloaded=False
#                 )


        
@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_other_posts(sender, instance, created, **kwargs):
    existing_other_posts = OtherPost.objects.select_related('category', 'group').filter(
        group=instance.group
    )
    
    for other_post in existing_other_posts:
        # Try to retrieve an existing mapping for this post and customer frame
        mapping = CustomerOtherPostFrameMapping.objects.filter(
            customer_frame=instance,
            other_post=other_post
        ).first()

        if mapping:
            # Update existing mapping
            mapping.customer_frame = instance
            if mapping.is_downloaded:
                mapping.is_downloaded = False
            mapping.save()
        else:
            # Create new mapping
            new_mapping = CustomerOtherPostFrameMapping.objects.create(
                customer=instance.customer,
                other_post=other_post,
                customer_frame=instance,
                is_downloaded=False
            )
            
            

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
