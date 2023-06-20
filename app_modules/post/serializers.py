from rest_framework import serializers
from django.utils import timezone

from account.models import User, CustomerFrame
from .models import Category, Post, Event, OtherPost, CustomerPostFrameMapping
from account.serializers import CustomerFrameSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'banner_image', 'sub_category', 'is_active']
        
 
class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        
               
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'event_date', 'thumbnail']
        
    def validate_event_date(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Event date cannot be in the past.")
        return value
        

class PostSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    event_details = serializers.SerializerMethodField()
    customer_details = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'event', 'file_type', 'file', 'group', 'is_active', 'added_on',
                  'group_name', 'customer_details', 'event_details', 'is_active']

    def get_customer_details(self, obj):
        user = self.context.get("user")
        request = self.context.get('request')
        customer_obj = User.objects.get(id=user.id)
        frame_objs = CustomerFrame.objects.select_related('customer', 'group').filter(group=obj.group, customer=user)
        
        if not obj.group:
            return []
        return CustomerFrameSerializer(frame_objs, many=True).data
        

    def get_group_name(self, obj):
        return obj.group.name if obj.group else None

    def get_event_details(self, obj):
        request = self.context.get('request')
        event = obj.event

        event_details = {
            "id": event.id,
            "name": event.name,
            "date": event.event_date,
        }

        if event.thumbnail:
            event_details["thumbnail"] = request.build_absolute_uri(event.thumbnail.url)

        return event_details

    

class OtherPostSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    
    class Meta:
        model  = OtherPost
        fields = ['id', 'category', 'category_name', 'name', 'file_type', 'file', 'group', 
            'group_name', 'is_active'
        ]
        
    def get_group_name(self, obj):
        if obj.group:
            return obj.group.name
        else:
            return None
        
    def get_category_name(self, obj):
        return obj.category.name
    
    
class CustomerPostFrameMappingSerializer(serializers.ModelSerializer):
    customer_frame_image = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = CustomerPostFrameMapping
        fields = ['id', 'customer', 'post', 'customer_frame', 'is_downloaded', 'customer_frame_image']
        
    
    def get_customer_frame_image(self, obj):
        request = self.context.get('request')
        data = CustomerFrame.objects.filter(customer=obj.customer)
        urls = []
        for image in data:
            urls.append(request.build_absolute_uri(image.frame_img.url))
        return urls

        

        