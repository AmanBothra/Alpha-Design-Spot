from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    Post, CustomerPostFrameMapping, CustomerOtherPostFrameMapping, OtherPost, BusinessPost,
    BusinessPostFrameMapping
)
from django.db.models import Q
from django.db.utils import IntegrityError




@receiver(post_save, sender=Post)
def mapping_post_with_customer_frame(sender, instance, created, **kwargs):
    if not created:
        return

    customer_group = instance.group
    customer_frames = customer_group.customer_frame_group.all()

    customer_frame_mappings = []
    for customer_frame in customer_frames:
        customer_frame_mappings.append(CustomerPostFrameMapping(
            customer_id=customer_frame.customer_id,
            post=instance,
            customer_frame=customer_frame,
        ))

    with transaction.atomic():
        CustomerPostFrameMapping.objects.bulk_create(customer_frame_mappings)


@receiver(post_save, sender=OtherPost)
def mapping_other_post_with_customer_frame(sender, instance, created, **kwargs):
    customer_group = instance.group
    customer_ids = customer_group.customer_frame_group.values_list('customer_id', flat=True)

    for customer_id in customer_ids:
        customer_frames = customer_group.customer_frame_group.filter(customer_id=customer_id)

        mappings_to_create = []
        for customer_frame in customer_frames:
            mappings_to_create.append(CustomerOtherPostFrameMapping(
                customer_id=customer_id,
                other_post=instance,
                customer_frame=customer_frame,
            ))

        # Bulk create mappings for the current customer_id
        with transaction.atomic():
            CustomerOtherPostFrameMapping.objects.bulk_create(mappings_to_create)



# @receiver(post_save, sender=BusinessPost)
# def mapping_business_post_with_customer_frame(sender, instance, created, **kwargs):
#     if created:
#         customer_group = instance.group
#         customer_ids = customer_group.customer_frame_group.values_list('customer_id', flat=True)

#         for customer_id in customer_ids:
#             customer_frames = customer_group.customer_frame_group.filter(customer_id=customer_id)

#             for customer_frame in customer_frames:
#                 mapping, created = BusinessPostFrameMapping.objects.get_or_create(
#                     customer_id=customer_id,
#                     post=instance,
#                     customer_frame=customer_frame,
#                 )
#                 if not created:
#                     mapping.save()


@receiver(post_save, sender=BusinessPost)
def mapping_business_post_with_customer_frame(sender, instance, created, **kwargs):
    customer_group = instance.group
    customer_ids = customer_group.customer_frame_group.values_list('customer_id', flat=True)

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
