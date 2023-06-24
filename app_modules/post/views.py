from datetime import date, timedelta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from app_modules.post import serializers
from lib.viewsets import BaseModelViewSet
from app_modules.post.models import Category, Event, Post, OtherPost, CustomerPostFrameMapping
from .filters import EventFilter


class CategoeryViewset(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'name': ["in", "exact"]
    }
    
    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     serializer = self.get_serializer(queryset, many=True)

    #     # Retrieve all sub-categories and add them to the response
    #     all_sub_categories = Category.objects.filter(sub_category__isnull=False)
    #     sub_category_serializer = serializers.CategorySerializer(all_sub_categories, many=True)
    #     response_data = {
    #         'categories': serializer.data,
    #         'all_sub_categories': sub_category_serializer.data
    #     }
    #     return Response(response_data)
    
    
class SubcategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(sub_category__isnull=False)
    serializer_class = serializers.SubcategorySerializer
    
class EventViewset(BaseModelViewSet):
    # queryset = Event.objects.all()
    serializer_class = serializers.EventSerializer
    filterset_class = EventFilter
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ('event_date', 'name')
    
    def get_queryset(self):
        date_type = self.request.GET.get('date_type')
        today = date.today()
        tomorrow = today + timedelta(days=1)
        queryset = Event.objects.all().order_by('-event_date')

        if date_type == "today":
            queryset = queryset.filter(event_date=today)
        elif date_type == "tomorrow":
            queryset = queryset.filter(event_date=tomorrow)
        elif date_type == "upcoming":
            queryset = queryset.filter(event_date__gte=tomorrow)

        return queryset
    
            
    
class PostViewset(BaseModelViewSet):
    queryset = Post.objects.select_related('event', 'group').all()
    serializer_class = serializers.PostSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['group__name', 'event__name', 'is_active', 'file_type']
    
    def get_serializer_context(self):
        context = super(PostViewset, self).get_serializer_context()
        return context
    
    def create(self, request, *args, **kwargs):
        event_id = request.data.get('event')
        group_id = request.data.get('group')

        if event_id and group_id:
            existing_post = Post.objects.filter(event_id=event_id, group_id=group_id).exists()
            if existing_post:
                raise ValidationError({"event":"A post with the same event and group already exists."})

        return super().create(request, *args, **kwargs)
     

class OtherPostViewset(BaseModelViewSet):
    queryset = OtherPost.objects.select_related('category', 'group').all()
    serializer_class = serializers.OtherPostSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['group__name', 'category__name', 'is_active', 'file_type']
    
    
class CustomerPostFrameMappingViewSet(BaseModelViewSet):
    queryset = CustomerPostFrameMapping.objects
    serializer_class = serializers.CustomerPostFrameMappingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['post__event__event_date']
    http_method_names = ['get', 'patch']
    
    
    def get_serializer_context(self):
        context = super(CustomerPostFrameMappingViewSet, self).get_serializer_context()
        context["user"] = self.request.user
        return context
    
    
    def get_queryset(self):
        customer = self.request.user
        event_id = self.request.query_params.get('event_id')
        queryset = self.queryset.select_related('customer', 'post', 'customer_frame').filter(
            customer=customer, post__event=event_id)
        
        return queryset
    