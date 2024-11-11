from celery import shared_task
from django.db import transaction
from .models import *

# @shared_task
def map_post_with_customer_frames(post_id):
    try:
        instance = Post.objects.select_related('event', 'group').get(id=post_id)
    except Post.DoesNotExist:
        return f"Post with id {post_id} does not exist."

    # Fetch customer frames efficiently with only necessary fields
    customer_frames = instance.group.customer_frame_group.all().values_list('customer_id', 'id')

    # Prepare mappings in a list
    customer_frame_mappings = [
        CustomerPostFrameMapping(
            customer_id=customer_id,
            post=instance,
            customer_frame_id=frame_id,
        )
        for customer_id, frame_id in customer_frames
    ]

    # Bulk create with batch_size for efficient large data handling
    with transaction.atomic():
        CustomerPostFrameMapping.objects.bulk_create(customer_frame_mappings, batch_size=200)

    
# @shared_task
def map_other_post_with_customer_frames(other_post_id):
    try:
        instance = OtherPost.objects.get(id=other_post_id)
    except OtherPost.DoesNotExist:
        return f"OtherPost with id {other_post_id} does not exist."

    customer_group = instance.group

    # Retrieve only unique customer IDs associated with the customer frames
    customer_ids = customer_group.customer_frame_group.values_list('customer_id', flat=True).distinct()

    # Prepare all mappings to create, grouped by customer_id
    all_mappings = []
    for customer_id in customer_ids:
        # Retrieve customer frames for each customer_id with only necessary fields
        customer_frames = customer_group.customer_frame_group.filter(customer_id=customer_id).values_list('id', flat=True)
        
        # Append mappings to the list
        for frame_id in customer_frames:
            all_mappings.append(CustomerOtherPostFrameMapping(
                customer_id=customer_id,
                other_post=instance,
                customer_frame_id=frame_id,
            ))

    # Bulk create all mappings with batch_size
    with transaction.atomic():
        CustomerOtherPostFrameMapping.objects.bulk_create(all_mappings, batch_size=1000)


# @shared_task
def map_business_post_with_customer_frames(business_post_id):
    try:
        instance = BusinessPost.objects.get(id=business_post_id)
    except BusinessPost.DoesNotExist:
        return f"BusinessPost with id {business_post_id} does not exist."

    customer_group = instance.group

    # Fetch all customer IDs related to the customer frames in one query
    customer_ids = customer_group.customer_frame_group.values_list('customer_id', flat=True).distinct()

    # Fetch existing mappings for this post and customer IDs to avoid duplicate creation
    existing_mappings = set(
        BusinessPostFrameMapping.objects.filter(
            post=instance,
            customer_id__in=customer_ids
        ).values_list('customer_id', 'customer_frame_id')
    )

    # Prepare a list of mappings to create
    mappings_to_create = []
    for customer_id in customer_ids:
        # Fetch frame IDs for the customer
        customer_frame_ids = customer_group.customer_frame_group.filter(customer_id=customer_id).values_list('id', flat=True)

        # Add mappings if they don't already exist
        for frame_id in customer_frame_ids:
            if (customer_id, frame_id) not in existing_mappings:
                mappings_to_create.append(BusinessPostFrameMapping(
                    customer_id=customer_id,
                    post=instance,
                    customer_frame_id=frame_id
                ))

    # Bulk create all mappings in batches
    with transaction.atomic():
        BusinessPostFrameMapping.objects.bulk_create(mappings_to_create, batch_size=1000)