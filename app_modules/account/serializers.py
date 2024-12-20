from datetime import date

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from app_modules.post.models import Post, CustomerPostFrameMapping, CustomerOtherPostFrameMapping, OtherPost
from .models import (
    User, CustomerFrame, CustomerGroup, PaymentMethod, Plan, Subscription
)
from django.db.models import F


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    whatsapp_number = serializers.CharField(allow_null=True, required=False)
    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'email', 'user_type', 'whatsapp_number', 'address', 'pincode',
            'city', 'dob', 'no_of_post', 'password', "is_verify", "created", "modified", "is_deleted"
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }
        
    def validate_whatsapp_number(self, value):
        if value is None:
            return value
            
        if User.objects.filter(whatsapp_number=value).exists():
            raise ValueError("Mobile number already registered.")
        return value

    def create(self, validated_data):
        validated_data['user_type'] = 'customer'
        user = User.objects.create_user(**validated_data)
        return user


class AdminRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'user_type', 'email', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        validated_data['user_type'] = 'admin'
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email', 'user_type', 'whatsapp_number', 'address',
            'pincode', 'city', 'dob', 'no_of_post', "is_verify", 'is_active', 'added_on'
        ]


class CustomerFrameSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    mobile_number = serializers.CharField(source='customer.whatsapp_number', read_only=True)
    business_category_name = serializers.CharField(source='business_category.name', read_only=True)

    class Meta:
        model = CustomerFrame
        fields = (
            'id', 'customer', 'frame_img', 'group', 'group_name', 'display_name', 'mobile_number', 'business_category',
            'profession_type', 'business_category_name', 'updated_on'
        )

    def validate(self, data):
        """Move validations from create to validate method"""
        customer = data.get('customer')
        business_category = data.get('business_category')
        display_name = data.get('display_name')
        profession_type = data.get('profession_type')
        
        # Get instance for update case
        instance = getattr(self, 'instance', None)

        # Display name validation
        if display_name:
            display_name_query = CustomerFrame.objects.filter(
                customer=customer,
                display_name=display_name
            )
            if instance:
                display_name_query = display_name_query.exclude(id=instance.id)
            if display_name_query.exists():
                raise serializers.ValidationError({
                    "display_name": "This display name is already assigned."
                })

        # Post limit validation - only for creation
        if not instance:  # Only check on create
            if CustomerFrame.objects.filter(customer=customer).count() >= customer.no_of_post:
                raise serializers.ValidationError({
                    "customer": f"Maximum posts limit ({customer.no_of_post}) reached."
                })

        # Business category and profession type validation
        if display_name and profession_type:
            category_query = CustomerFrame.objects.filter(
                customer=customer,
                business_category=business_category,
                profession_type=profession_type
            )
            if instance:
                category_query = category_query.exclude(id=instance.id)
            if category_query.exists():
                raise serializers.ValidationError({
                    "customer": f"This {business_category.name} and {profession_type} already assigned."
                })

        return data


    def update(self, instance, validated_data):
        current_date = date.today()
        old_group_id = instance.group.id if instance.group else None

        # Update the instance with validated data
        instance = super().update(instance, validated_data)

        if old_group_id and 'group' in validated_data:
            new_group_id = validated_data['group'].id if validated_data['group'] else None
            
            new_post_ids = Post.objects.filter(
                group_id=new_group_id,
                event__event_date__gte=current_date
            ).values_list('id', flat=True)
            
            new_other_post_ids = OtherPost.objects.filter(group_id=new_group_id).values_list('id', flat=True)
            
            old_post_ids = Post.objects.filter(
                group_id=old_group_id,
                event__event_date__gte=current_date
            ).values_list('id', flat=True)
            
            old_other_post_ids = OtherPost.objects.filter(group_id=old_group_id).values_list('id', flat=True)
            
            old_post_mapping = CustomerPostFrameMapping.objects.filter(
                customer_frame_id=instance.id,
                post_id__in=old_post_ids
            )
            
            old_other_post_mapping = CustomerOtherPostFrameMapping.objects.filter(
                customer_frame_id=instance.id,
                other_post_id__in=old_other_post_ids
            )
            
            for mapping, new_post_id in zip(old_post_mapping, new_post_ids):
                mapping.post_id = new_post_id
                mapping.save()
                
            for mapping, new_other_post_id in zip(old_other_post_mapping, new_other_post_ids):
                mapping.other_post_id = new_other_post_id
                mapping.save()
                    
            
        return instance


class CustomerGroupSerializer(serializers.ModelSerializer):
    frame_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomerGroup
        fields = ('id', 'name', 'frame_count')

    def get_frame_count(self, obj):
        return obj.customer_frame_group.count()


class CuatomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'whatsapp_number')


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ('id', 'name')


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ('id', 'name', 'duration_in_months', 'price')


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    payment_method_name = serializers.CharField(source="payment_method.name", read_only=True)
    is_expired = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source="user.first_name", read_only=True)
    display_name = serializers.CharField(source="frame.display_name", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'order_number', 'user', 'customer_name', 'frame', 'plan', 'plan_name', 'payment_method',
            'start_date', 'end_date', 'transaction_number', 'file', 'is_active', 'is_expired', 'days_left',
            'display_name', 'payment_method_name'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_date = date.today()

    def validate(self, data):
        current_date = date.today()

        start_date = data.get('start_date')
        end_date = data.get('end_date')
        user = data.get('user')
        frame = data.get('frame')

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("End date must be greater than or equal to the start date.")

            # if start_date < current_date:
            #     raise ValidationError("Start date cannot be in the past.")

            # if end_date < current_date:
            #     raise ValidationError("End date cannot be in the past.")

        if user and frame:
            existing_subscription = Subscription.objects.filter(user=user, frame=frame).first()

            if existing_subscription:
                if existing_subscription.end_date >= current_date:
                    raise ValidationError({
                                              "subscription": f"A subscription for this {user.email} and {frame.display_name} combination already exists and is not expired."})

        return data

    def get_is_expired(self, obj):
        return obj.end_date < self.current_date

    def get_days_left(self, obj):
        days_left = (obj.end_date - self.current_date).days
        if days_left < 0:
            return 0
        return days_left
