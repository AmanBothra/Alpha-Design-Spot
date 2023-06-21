from django.db.models.signals import post_save
from django.dispatch import receiver


from .models import Post, CustomerPostFrameMapping, CustomerOtherPostFrameMapping, OtherPost



@receiver(post_save, sender=Post)
def mapping_post_with_customer_frame(sender, instance, created, **kwargs):
    customer_group = instance.group
    customer_ids = customer_group.customer_frame_group.values_list('customer_id', flat=True)

    # Create CustomerPostFrameMapping instances for each customer ID
    for customer_id in customer_ids:
        customer_frames = customer_group.customer_frame_group.filter(customer_id=customer_id)
        for customer_frame in customer_frames:
            mapping = CustomerPostFrameMapping.objects.create(
                customer_id=customer_id,
                post=instance,
                customer_frame=customer_frame,
                is_downloaded=False
            )
            mapping.save()

        
@receiver(post_save, sender=OtherPost)
def mapping_other_post_with_customer_frame(sender, instance, created, **kwargs):
    
    customer_group = instance.group
    customer_ids = customer_group.customer_frame_group.values_list('customer_id', flat=True)

    # Create CustomerPostFrameMapping instances for each customer ID
    for customer_id in customer_ids:
        customer_frames = customer_group.customer_frame_group.filter(customer_id=customer_id)
        for customer_frame in customer_frames:
            mapping = CustomerOtherPostFrameMapping.objects.create(
                customer_id=customer_id,
                other_post=instance,
                customer_frame=customer_frame,
                is_downloaded=False
            )
            mapping.save()

    