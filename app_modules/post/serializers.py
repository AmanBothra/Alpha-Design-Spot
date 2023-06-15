from rest_framework import serializers
from django.utils import timezone


from .models import Category, Post, Event, OtherPost


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'banner_image', 'sub_category', 'is_active']
        
        
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'event_date']
        
    def validate_event_date(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Event date cannot be in the past.")
        return value
        

class PostSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    event_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'event', 'file_type', 'file', 'group', 'is_active', 'added_on',
                  'group_name', 'event_name', 'is_active'
        ]
        
        
    def get_group_name(self, obj):
        if obj.group:
            return obj.group.name
        else:
            return None
        
    def get_event_name(self, obj):
        return obj.event.name
    

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
    