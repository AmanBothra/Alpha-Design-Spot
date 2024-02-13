import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver

from app_modules.post.models import (
    Event, Post, OtherPost, CustomerPostFrameMapping, CustomerOtherPostFrameMapping, BusinessPost,
    BusinessPostFrameMapping
)
from .models import CustomerFrame


@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_post(sender, instance, created, **kwargs):
    if created:
        current_date = datetime.date.today()
        future_events = Event.objects.filter(event_date__gte=current_date)

        existing_posts = Post.objects.select_related('event', 'group').filter(
            group=instance.group, event__in=future_events
        )

        batch_size = 100
        for i in range(0, len(existing_posts), batch_size):
            batch_posts = existing_posts[i:i + batch_size]
            mappings_to_create = []

            for post in batch_posts:
                mapping = CustomerPostFrameMapping.objects.filter(
                    customer_frame=instance,
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
                    mappings_to_create.append(CustomerPostFrameMapping(
                        customer=instance.customer,
                        post=post,
                        customer_frame=instance,
                        is_downloaded=False
                    ))

            # Bulk create mappings in the current batch
            CustomerPostFrameMapping.objects.bulk_create(mappings_to_create)


@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_other_posts(sender, instance, created, **kwargs):
    if created:
        existing_other_posts = OtherPost.objects.select_related('category', 'group').filter(
            group=instance.group
        )

        batch_size = 100
        for i in range(0, len(existing_other_posts), batch_size):
            batch_other_posts = existing_other_posts[i:i + batch_size]
            mappings_to_create = []

            for other_post in batch_other_posts:
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
                    mappings_to_create.append(CustomerOtherPostFrameMapping(
                        customer=instance.customer,
                        other_post=other_post,
                        customer_frame=instance,
                        is_downloaded=False
                    ))

            # Bulk create mappings in the current batch
            CustomerOtherPostFrameMapping.objects.bulk_create(mappings_to_create)


@receiver(post_save, sender=CustomerFrame)
def mapping_customer_frame_with_business_posts(sender, instance, created, **kwargs):
    if created:
        customer = instance.customer
        customer_group = instance.group
        profession_type = instance.profession_type
        business_category = instance.business_category

        business_posts = BusinessPost.objects.filter(
            business_category=business_category, profession_type=profession_type, group=customer_group
        ).select_related('business_category', 'group')

        for business_post in business_posts:
            mapping, _ = BusinessPostFrameMapping.objects.get_or_create(
                customer=customer,
                post=business_post,
                defaults={'customer_frame': instance}
            )
