from celery import shared_task
from .models import *

@shared_task
def map_post_with_customer_frames(post_id):
    try:
        instance = Post.objects.select_related('event', 'group').get(id=post_id)
    except Post.DoesNotExist:
        return f"Post with id {post_id} does not exist."

    customer_frames = instance.group.customer_frame_group.all().values_list('customer_id', 'id')

    customer_frame_mappings = [
        CustomerPostFrameMapping(
            customer_id=customer_id,
            post=instance,
            customer_frame_id=frame_id,
        )
        for customer_id, frame_id in customer_frames
    ]

    CustomerPostFrameMapping.objects.bulk_create(
        customer_frame_mappings, 
        batch_size=200
    )

@shared_task
def map_other_post_with_customer_frames(other_post_id):
    try:
        instance = OtherPost.objects.get(id=other_post_id)
    except OtherPost.DoesNotExist:
        return f"OtherPost with id {other_post_id} does not exist."

    customer_group = instance.group

    customer_ids = list(customer_group.customer_frame_group.values_list(
        'customer_id', 
        flat=True
    ).distinct())

    all_mappings = []
    for customer_id in customer_ids:
        customer_frames = customer_group.customer_frame_group.filter(
            customer_id=customer_id
        ).values_list('id', flat=True)

        all_mappings.extend([
            CustomerOtherPostFrameMapping(
                customer_id=customer_id,
                other_post=instance,
                customer_frame_id=frame_id,
            )
            for frame_id in customer_frames
        ])

    CustomerOtherPostFrameMapping.objects.bulk_create(
        all_mappings, 
        batch_size=350
    )

@shared_task
def map_business_post_with_customer_frames(business_post_id):
    try:
        instance = BusinessPost.objects.get(id=business_post_id)
    except BusinessPost.DoesNotExist:
        return f"BusinessPost with id {business_post_id} does not exist."

    customer_group = instance.group

    customer_ids = list(customer_group.customer_frame_group.values_list(
        'customer_id', 
        flat=True
    ).distinct())

    existing_mappings = set(
        BusinessPostFrameMapping.objects.filter(
            post=instance,
            customer_id__in=customer_ids
        ).values_list('customer_id', 'customer_frame_id')
    )

    mappings_to_create = []
    for customer_id in customer_ids:
        customer_frame_ids = customer_group.customer_frame_group.filter(
            customer_id=customer_id
        ).values_list('id', flat=True)

        mappings_to_create.extend([
            BusinessPostFrameMapping(
                customer_id=customer_id,
                post=instance,
                customer_frame_id=frame_id
            )
            for frame_id in customer_frame_ids
            if (customer_id, frame_id) not in existing_mappings
        ])

    BusinessPostFrameMapping.objects.bulk_create(
        mappings_to_create, 
        batch_size=350
    )
