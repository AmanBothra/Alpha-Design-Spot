from rest_framework import serializers
from datetime import date

from .models import (
    User, CustomerFrame, CustomerGroup, PaymentMethod, Plan, Subscription, AppVersion
)


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'email', 'user_type', 'whatsapp_number', 'address', 'pincode',
            'city', 'dob', 'no_of_post', 'password',
            "is_verify", "created", "modified"
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }

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
    group_name = serializers.SerializerMethodField()
    mobile_number = serializers.SerializerMethodField()
    business_category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerFrame
        fields = (
            'id', 'customer', 'frame_img', 'group', 'group_name', 'display_name', 'mobile_number', 'business_category',
            'profession_type', 'business_category_name'
        )
        
    def create(self, validated_data):
        customer = validated_data.get('customer')
        business_category = validated_data.get('business_category')
        display_name = validated_data.get('display_name')
        profession_type = validated_data.get('profession_type')
        no_of_post = customer.no_of_post
        
        
        if display_name:
            existing_frame_with_display_name = CustomerFrame.objects.filter(
                customer=customer,
                display_name=display_name
            ).first()
            if existing_frame_with_display_name:
                raise serializers.ValidationError(
                    {"display_name": f"This display name is already assigned to another customer frame."}
                )
            
        existing_frame_count = CustomerFrame.objects.filter(customer=customer).count()
        if existing_frame_count >= no_of_post:
            raise serializers.ValidationError({"customer": f"The customer has already reached the maximum number of posts {no_of_post}."})
        
        if display_name and profession_type:
            existing_frame = CustomerFrame.objects.filter(
                customer=customer,
                business_category=business_category,
                profession_type=profession_type
            ).first()
            
            if existing_frame:
                raise serializers.ValidationError(
                    {"customer": f"This {business_category.name} and {profession_type} already assigned to the customer."}
                )
        
        return super().create(validated_data)
        
    def get_group_name(self, obj):
        return getattr(obj.group, 'name', None)

    def get_business_category_name(self, obj):
        return getattr(obj.business_category, 'name', None)
        
    def get_mobile_number(self, obj):
        return obj.customer.whatsapp_number
    
        
        
        
class CustomerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerGroup
        fields = ('id', 'name')
        
        
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
    payment_method = serializers.CharField(source="payment_method.name", read_only=True)
    is_expired = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source="user.first_name", read_only=True)
    display_name = serializers.CharField(source="frame.display_name", read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'order_number', 'user', 'customer_name', 'frame', 'plan', 'plan_name', 'payment_method',
            'start_date', 'end_date', 'transaction_number', 'file', 'is_active', 'is_expired', 'days_left',
            'display_name'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_date = date.today()
        
        
    def get_is_expired(self, obj):
        return obj.end_date < self.current_date

    def get_days_left(self, obj):
        return (obj.end_date - self.current_date).days
    
    
        
class AppVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppVersion
        fields = [
            'id', 'current_version', 'required_version', 'app_type'
        ]