from celery import shared_task
from django.db import transaction
from app_modules.post.models import *
import datetime

# @shared_task
def mapping_customer_frame_with_post(customer_frame_id):
    try:
        # Use select_related to reduce queries
        instance = CustomerFrame.objects.select_related(
            'group', 'customer'
        ).get(id=customer_frame_id)
    except CustomerFrame.DoesNotExist:
        return f"CustomerFrame with id {customer_frame_id} does not exist."

    # Use values() to optimize memory
    current_date = datetime.date.today()
    future_events = Event.objects.filter(event_date__gte=current_date).values_list('id', flat=True)

    # Optimize query with values()
    existing_posts = Post.objects.filter(
        group=instance.group, event__in=future_events
    ).values('id', 'group_id')

    # Use bulk operations with larger batch size
    batch_size = 500
    mappings_to_create = []

    for i in range(0, len(existing_posts), batch_size):
        batch_posts = existing_posts[i:i + batch_size]
        
        with transaction.atomic():
            # Bulk get existing mappings
            existing_mappings = set(CustomerPostFrameMapping.objects.filter(
                customer_frame=instance,
                post_id__in=[p['id'] for p in batch_posts]
            ).values_list('post_id', flat=True))

            for post in batch_posts:
                if post['id'] not in existing_mappings:
                    mappings_to_create.append(
                        CustomerPostFrameMapping(
                            customer_frame=instance,
                            post_id=post['id'],
                            customer=instance.customer,
                            is_downloaded=False
                        )
                    )

            if mappings_to_create:
                CustomerPostFrameMapping.objects.bulk_create(
                    mappings_to_create,
                    batch_size=batch_size
                )

    return f"Mapping completed for CustomerFrame with id {customer_frame_id}"


# @shared_task
def mapping_customer_frame_with_other_posts(customer_frame_id):
    try:
        # Use select_related to reduce queries
        instance = CustomerFrame.objects.select_related(
            'customer', 'group'
        ).get(id=customer_frame_id)
    except CustomerFrame.DoesNotExist:
        return f"CustomerFrame with id {customer_frame_id} does not exist."

    # Get only necessary fields using values()
    existing_other_posts = OtherPost.objects.filter(
        group=instance.group
    ).values_list('id', flat=True)

    # Increased batch size for better performance
    batch_size = 500
    mappings_to_create = []

    # Get existing mappings in one query
    existing_mappings = set(
        CustomerOtherPostFrameMapping.objects.filter(
            customer_frame=instance,
            other_post_id__in=existing_other_posts
        ).values_list('other_post_id', flat=True)
    )

    # Process in batches
    for i in range(0, len(existing_other_posts), batch_size):
        batch_other_posts = existing_other_posts[i:i + batch_size]
        
        with transaction.atomic():
            # Create new mappings for posts that don't have mappings
            for post_id in batch_other_posts:
                if post_id not in existing_mappings:
                    mappings_to_create.append(
                        CustomerOtherPostFrameMapping(
                            customer_frame=instance,
                            other_post_id=post_id,
                            customer=instance.customer,
                            is_downloaded=False
                        )
                    )

            # Bulk create new mappings
            if mappings_to_create:
                CustomerOtherPostFrameMapping.objects.bulk_create(
                    mappings_to_create, 
                    batch_size=batch_size,
                    ignore_conflicts=True
                )

            # Bulk update existing mappings that are downloaded
            CustomerOtherPostFrameMapping.objects.filter(
                customer_frame=instance,
                other_post_id__in=batch_other_posts,
                is_downloaded=True
            ).update(is_downloaded=False)

    return f"Mapping completed for CustomerFrame with id {customer_frame_id}"

# @shared_task
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