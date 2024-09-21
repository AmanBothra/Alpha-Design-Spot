from celery import shared_task
from django.db import transaction
from app_modules.post.models import *
import datetime

@shared_task
def mapping_customer_frame_with_post(customer_frame_id):
    try:
        instance = CustomerFrame.objects.get(id=customer_frame_id)
    except CustomerFrame.DoesNotExist:
        return f"CustomerFrame with id {customer_frame_id} does not exist."

    current_date = datetime.date.today()
    future_events = Event.objects.filter(event_date__gte=current_date)

    existing_posts = Post.objects.select_related('event', 'group').filter(
        group=instance.group, event__in=future_events
    )

    batch_size = 100
    for i in range(0, len(existing_posts), batch_size):
        batch_posts = existing_posts[i:i + batch_size]
        mappings_to_create = []

        with transaction.atomic():
            for post in batch_posts:
                mapping, created = CustomerPostFrameMapping.objects.get_or_create(
                    customer_frame=instance,
                    post=post,
                    defaults={
                        'customer': instance.customer,
                        'is_downloaded': False
                    }
                )

                if not created and mapping.is_downloaded:
                    mapping.is_downloaded = False
                    mapping.save()

            if mappings_to_create:
                CustomerPostFrameMapping.objects.bulk_create(mappings_to_create)

    return f"Mapping completed for CustomerFrame with id {customer_frame_id}"


@shared_task
def mapping_customer_frame_with_other_posts(customer_frame_id):
    try:
        instance = CustomerFrame.objects.get(id=customer_frame_id)
    except CustomerFrame.DoesNotExist:
        return f"CustomerFrame with id {customer_frame_id} does not exist."

    existing_other_posts = OtherPost.objects.select_related('category', 'group').filter(
        group=instance.group
    )

    batch_size = 100
    for i in range(0, len(existing_other_posts), batch_size):
        batch_other_posts = existing_other_posts[i:i + batch_size]
        mappings_to_create = []

        with transaction.atomic():
            for other_post in batch_other_posts:
                # Try to retrieve an existing mapping for this post and customer frame
                mapping, created = CustomerOtherPostFrameMapping.objects.get_or_create(
                    customer_frame=instance,
                    other_post=other_post,
                    defaults={
                        'customer': instance.customer,
                        'is_downloaded': False
                    }
                )

                if not created:
                    # Update existing mapping
                    if mapping.is_downloaded:
                        mapping.is_downloaded = False
                        mapping.save()

    return f"Mapping completed for CustomerFrame with id {customer_frame_id}"


@shared_task
def map_customer_frame_with_business_posts(customer_frame_id):
    try:
        instance = CustomerFrame.objects.get(id=customer_frame_id)
    except CustomerFrame.DoesNotExist:
        return f"CustomerFrame with id {customer_frame_id} does not exist."

    customer = instance.customer
    customer_group = instance.group
    profession_type = instance.profession_type
    business_category = instance.business_category

    business_posts = BusinessPost.objects.filter(
        business_category=business_category, profession_type=profession_type, group=customer_group
    ).select_related('business_category', 'group')

    batch_size = 100
    for i in range(0, len(business_posts), batch_size):
        batch_business_posts = business_posts[i:i + batch_size]
        mappings_to_create = []

        for business_post in batch_business_posts:
            # Try to retrieve an existing mapping for this post and customer frame
            mapping = BusinessPostFrameMapping.objects.filter(
                customer=customer,
                post=business_post
            ).first()

            if mapping:
                # Update existing mapping
                mapping.customer_frame = instance
                if mapping.is_downloaded:
                    mapping.is_downloaded = False
                mapping.save()
            else:
                # Create new mapping
                mappings_to_create.append(BusinessPostFrameMapping(
                    customer=customer,
                    post=business_post,
                    customer_frame=instance,
                ))

        # Bulk create mappings in the current batch
        if mappings_to_create:
            with transaction.atomic():
                BusinessPostFrameMapping.objects.bulk_create(mappings_to_create)

    return f"Mapping completed for CustomerFrame with id {customer_frame_id}"