from celery import shared_task
from silk.profiling.profiler import silk_profile
from .models import *

# @shared_task
@silk_profile(name='Map Post with Customer Frames Task')
def map_post_with_customer_frames(post_id):
    try:
        with silk_profile(name='Fetch Post Instance'):
            instance = Post.objects.select_related('event', 'group').get(id=post_id)
    except Post.DoesNotExist:
        return f"Post with id {post_id} does not exist."

    with silk_profile(name='Fetch Customer Frames'):
        customer_frames = instance.group.customer_frame_group.all().values_list('customer_id', 'id')

    with silk_profile(name='Prepare Mappings'):
        customer_frame_mappings = [
            CustomerPostFrameMapping(
                customer_id=customer_id,
                post=instance,
                customer_frame_id=frame_id,
            )
            for customer_id, frame_id in customer_frames
        ]

    with silk_profile(name='Bulk Create Mappings'):
            CustomerPostFrameMapping.objects.bulk_create(
                customer_frame_mappings, 
                batch_size=200
            )

# @shared_task
@silk_profile(name='Map Other Post with Customer Frames Task')

def map_other_post_with_customer_frames(other_post_id):
    with silk_profile(name=f'Map Other Post {other_post_id} with Customer Frames'):
        try:
            with silk_profile(name='Fetch Other Post Instance'):
                instance = OtherPost.objects.get(id=other_post_id)
        except OtherPost.DoesNotExist:
            return f"OtherPost with id {other_post_id} does not exist."

        customer_group = instance.group

        with silk_profile(name='Fetch Unique Customer IDs'):
            # Retrieve only unique customer IDs associated with the customer frames
            customer_ids = list(customer_group.customer_frame_group.values_list(
                'customer_id', 
                flat=True
            ).distinct())

        with silk_profile(name='Prepare All Mappings'):
            # Prepare all mappings to create, grouped by customer_id
            all_mappings = []
            for customer_id in customer_ids:
                with silk_profile(name=f'Process Customer {customer_id}'):
                    # Retrieve customer frames for each customer_id
                    customer_frames = customer_group.customer_frame_group.filter(
                        customer_id=customer_id
                    ).values_list('id', flat=True)
                    
                    # Append mappings to the list
                    all_mappings.extend([
                        CustomerOtherPostFrameMapping(
                            customer_id=customer_id,
                            other_post=instance,
                            customer_frame_id=frame_id,
                        )
                        for frame_id in customer_frames
                    ])

        with silk_profile(name='Bulk Create All Mappings'):
            # Bulk create all mappings with batch_size
                CustomerOtherPostFrameMapping.objects.bulk_create(
                    all_mappings, 
                    batch_size=350
                )

# @shared_task
@silk_profile(name='Map Buesiness Post with Customer Frames Task')

def map_business_post_with_customer_frames(business_post_id):
    with silk_profile(name=f'Map Business Post {business_post_id} with Customer Frames'):
        try:
            with silk_profile(name='Fetch Business Post Instance'):
                instance = BusinessPost.objects.get(id=business_post_id)
        except BusinessPost.DoesNotExist:
            return f"BusinessPost with id {business_post_id} does not exist."

        customer_group = instance.group

        with silk_profile(name='Fetch Customer IDs'):
            # Fetch all customer IDs related to the customer frames in one query
            customer_ids = list(customer_group.customer_frame_group.values_list(
                'customer_id', 
                flat=True
            ).distinct())

        with silk_profile(name='Check Existing Mappings'):
            # Fetch existing mappings for this post and customer IDs
            existing_mappings = set(
                BusinessPostFrameMapping.objects.filter(
                    post=instance,
                    customer_id__in=customer_ids
                ).values_list('customer_id', 'customer_frame_id')
            )

        with silk_profile(name='Prepare New Mappings'):
            # Prepare a list of mappings to create
            mappings_to_create = []
            for customer_id in customer_ids:
                with silk_profile(name=f'Process Customer {customer_id} Frames'):
                    # Fetch frame IDs for the customer
                    customer_frame_ids = customer_group.customer_frame_group.filter(
                        customer_id=customer_id
                    ).values_list('id', flat=True)

                    # Add mappings if they don't already exist
                    mappings_to_create.extend([
                        BusinessPostFrameMapping(
                            customer_id=customer_id,
                            post=instance,
                            customer_frame_id=frame_id
                        )
                        for frame_id in customer_frame_ids
                        if (customer_id, frame_id) not in existing_mappings
                    ])

        with silk_profile(name='Bulk Create New Mappings'):
            # Bulk create all mappings in batches
                BusinessPostFrameMapping.objects.bulk_create(
                    mappings_to_create, 
                    batch_size=350
                )