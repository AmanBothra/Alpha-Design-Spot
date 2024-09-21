from celery import shared_task
from django.db import transaction
from .models import *

@shared_task
def map_post_with_customer_frames(post_id):
    try:
        instance = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return f"Post with id {post_id} does not exist."

    customer_group = instance.group
    customer_frames = customer_group.customer_frame_group.all()

    customer_frame_mappings = [
        CustomerPostFrameMapping(
            customer_id=customer_frame.customer_id,
            post=instance,
            customer_frame=customer_frame,
        )
        for customer_frame in customer_frames
    ]

    try:
        with transaction.atomic():
            created_mappings = CustomerPostFrameMapping.objects.bulk_create(customer_frame_mappings)
        return f"Created {len(created_mappings)} mappings for Post with id {post_id}"
    except Exception as e:
        # Log the error or handle it as appropriate for your application
        return f"Error creating mappings for Post with id {post_id}: {str(e)}"
    
    
@shared_task
def map_other_post_with_customer_frames(other_post_id):
    try:
        instance = OtherPost.objects.get(id=other_post_id)
    except OtherPost.DoesNotExist:
        return f"OtherPost with id {other_post_id} does not exist."

    customer_group = instance.group
    customer_ids = customer_group.customer_frame_group.values_list('customer_id', flat=True)

    total_mappings_created = 0

    for customer_id in customer_ids:
        customer_frames = customer_group.customer_frame_group.filter(customer_id=customer_id)

        mappings_to_create = [
            CustomerOtherPostFrameMapping(
                customer_id=customer_id,
                other_post=instance,
                customer_frame=customer_frame,
            )
            for customer_frame in customer_frames
        ]

        # Bulk create mappings for the current customer_id
        if mappings_to_create:
            with transaction.atomic():
                CustomerOtherPostFrameMapping.objects.bulk_create(mappings_to_create)
            total_mappings_created += len(mappings_to_create)

    return f"Created {total_mappings_created} mappings for OtherPost with id {other_post_id}"

@shared_task
def map_business_post_with_customer_frames(business_post_id):
    try:
        instance = BusinessPost.objects.get(id=business_post_id)
    except BusinessPost.DoesNotExist:
        return f"BusinessPost with id {business_post_id} does not exist."

    customer_group = instance.group
    customer_ids = customer_group.customer_frame_group.values_list('customer_id', flat=True)

    total_mappings_created = 0

    for customer_id in customer_ids:
        customer_frames = customer_group.customer_frame_group.filter(customer_id=customer_id)

        mappings_to_create = []
        for customer_frame in customer_frames:
            if not BusinessPostFrameMapping.objects.filter(
                customer_id=customer_id,
                post=instance,
                customer_frame=customer_frame
            ).exists():
                mappings_to_create.append(BusinessPostFrameMapping(
                    customer_id=customer_id,
                    post=instance,
                    customer_frame=customer_frame,
                ))

        # Bulk create mappings for the current customer_id
        if mappings_to_create:
            with transaction.atomic():
                BusinessPostFrameMapping.objects.bulk_create(mappings_to_create)
            total_mappings_created += len(mappings_to_create)

    return f"Created {total_mappings_created} mappings for BusinessPost with id {business_post_id}"