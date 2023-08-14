from django.db.models.signals import post_save, pre_save, Signal
from django.dispatch import receiver
import datetime

from .models import CustomerFrame
from app_modules.post.models import (
    Event, Post, OtherPost, CustomerPostFrameMapping, CustomerOtherPostFrameMapping, BusinessPost,
    BusinessPostFrameMapping
)

# Define custom signal
# group_update_signal = Signal()

# # Signal handler to capture group update
# @receiver(pre_save, sender=CustomerFrame)
# def capture_group_update(sender, instance, **kwargs):
#     try:
#         existing_instance = sender.objects.get(pk=instance.pk)
        
#         if existing_instance.group != instance.group:
#             # Trigger the custom signal with old and new group values
#             group_update_signal.send(sender=sender, 
#                                      old_group=existing_instance.group,
#                                      new_group=instance.group,
#                                      customer=instance.customer,
#                                      instance=instance  # Pass the instance here
#                                     )
#     except sender.DoesNotExist:
#         pass

# # Signal receiver for the custom signal
# @receiver(group_update_signal)
# def group_update_handler(sender, old_group, new_group, customer, instance, **kwargs):
#     # Update or create mappings based on existing_mappings
#     existing_mappings = CustomerPostFrameMapping.objects.filter(
#         customer=customer, post__group=old_group
#     )

#     for data in existing_mappings:
#         # Update the post group if it belongs to new group
#         if data.post.group == new_group:
#             data.post.group = new_group
#             data.post.save()

#     # Create new mapping for each post if no existing mappings found
#     if not existing_mappings:
#         current_date = datetime.date.today()
#         future_events = Event.objects.filter(event_date__gte=current_date)

#         # Get existing posts for the new group and future events
#         existing_posts = Post.objects.select_related('event', 'group').filter(
#             group=new_group, event__in=future_events
#         )

#         for post in existing_posts:
#             new_mapping, created = CustomerPostFrameMapping.objects.get_or_create(
#                 customer=customer,
#                 post=post,
#                 defaults={'customer_frame': instance}
#             )

#             if not created:
#                 new_mapping.customer_frame = instance
#                 if new_mapping.is_downloaded:
#                     new_mapping.is_downloaded = False
#                 new_mapping.save()

#     # Sample logic: Print a message
#     if old_group is not None and new_group is not None:
#         print(f"Group changed from {old_group} to {new_group}")
#     elif new_group is not None:
#         print(f"Group set to {new_group}")
        
        
@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_post(sender, instance, created, **kwargs):
    current_date = datetime.date.today()
    future_events = Event.objects.filter(event_date__gte=current_date)
    
    existing_posts = Post.objects.select_related('event', 'group').filter(
        group=instance.group, event__in=future_events
    )
    
    for post in existing_posts:
        # Try to retrieve an existing mapping for this post and customer frame
        mapping = CustomerPostFrameMapping.objects.filter(
            customer=instance.customer,
            post=post
        ).first()

        if mapping:
            # Update existing mapping
            mapping.customer_frame = instance
            if mapping.is_downloaded:
                mapping.is_downloaded = False
            mapping.save()
        else:
            # Create new mapping
            new_mapping = CustomerPostFrameMapping.objects.create(
                customer=instance.customer,
                post=post,
                customer_frame=instance,
                is_downloaded=False
            )



        
@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_other_posts(sender, instance, created, **kwargs):
    current_date = datetime.date.today()
    future_events = Event.objects.filter(event_date__gte=current_date)
    
    existing_other_posts = OtherPost.objects.select_related('category', 'group').filter(
        group=instance.group
    )
    
    for other_post in existing_other_posts:
        # Try to retrieve an existing mapping for this post and customer frame
        mapping = CustomerOtherPostFrameMapping.objects.filter(
            customer=instance.customer,
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
