from rest_framework import serializers
from django.utils import timezone

from account.models import User, CustomerFrame
from .models import Category, Post, Event, OtherPost, CustomerPostFrameMapping
from account.serializers import CustomerFrameSerializer



class SubcategorySerializer(serializers.ModelSerializer):
    banner_image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'banner_image']

    def get_banner_image(self, obj):
        request = self.context.get('request')
        if obj.banner_image:
            return request.build_absolute_uri(obj.banner_image.url)
        return None
        

class CategorySerializer(serializers.ModelSerializer):
    sub_categories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'banner_image', 'sub_categories', 'is_active']

    def get_sub_categories(self, obj):
        sub_categories = Category.objects.filter(sub_category=obj)
        serializer = SubcategorySerializer(sub_categories, many=True, context=self.context)
        return serializer.data

        
               
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
        request = self.context.get('request')
        frames = CustomerFrame.objects.select_related('customer', 'group').filter(customer=request.user, group__name=obj.group.name)
        urls = [request.build_absolute_uri(frame.frame_img.url) for frame in frames]
        return urls
        

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
    post_image = serializers.FileField(source="post.file", read_only=True)
    frame_image= serializers.FileField(source="customer_frame.frame_img", read_only=True)
    customer_number = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomerPostFrameMapping
        fields = [
            'id', 'customer', 'customer_number', 'post', 'customer_frame', 'is_downloaded', 'post_image', 'frame_image'
        ]
        
    def get_customer_number(self,obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.whatsapp_number
        return None
    
    

        