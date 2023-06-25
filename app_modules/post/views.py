from datetime import date, timedelta
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from app_modules.post import serializers
from lib.viewsets import BaseModelViewSet
from app_modules.post.models import Category, Event, Post, OtherPost, CustomerPostFrameMapping, CustomerOtherPostFrameMapping
from .filters import EventFilter


class CategoeryViewset(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'name': ["in", "exact"]
    }
    
    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        category = self.get_object()
        subcategories = Category.objects.filter(sub_category=category)
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)
    
    
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
    filterset_fields = ['is_downloaded']
    http_method_names = ['get', 'patch']
    
    
    def get_serializer_context(self):
        context = super(CustomerPostFrameMappingViewSet, self).get_serializer_context()
        context["user"] = self.request.user
        return context
    
    
    def get_queryset(self):
        customer = self.request.user
        event_id = self.request.query_params.get('event_id')
        
        queryset = self.queryset.prefetch_related('customer', 'post', 'customer_frame')
        if event_id:
            queryset = queryset.filter(customer=customer, post__event=event_id)
            
        return queryset

    

class CustomerOtherPostFrameMappingViewSet(BaseModelViewSet):
    queryset = CustomerOtherPostFrameMapping.objects
    serializer_class = serializers.CustomerOtherPostFrameMappingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['other_post__name']
    filterset_fields = ['is_downloaded']
    http_method_names = ['get', 'patch']
    
    
    def get_serializer_context(self):
        context = super(CustomerOtherPostFrameMappingViewSet, self).get_serializer_context()
        context["user"] = self.request.user
        return context
    
    
    def get_queryset(self):
        customer = self.request.user
        categoery_id = self.request.query_params.get('categoery_id')
        
        queryset = self.queryset.prefetch_related('customer', 'other_post', 'customer_frame')
        if categoery_id:
            queryset = queryset = queryset.filter(customer=customer, other_post__category=categoery_id)
            
        return queryset


class DownloadedDataViewSet(BaseModelViewSet):
    pagination_class = None

    def get_queryset(self):
        # Filter the data based on is_downloaded=True for both models
        customer = self.request.user
        file_type = self.request.query_params.get('file_type')
        
        customer_post_frame_data = CustomerPostFrameMapping.objects.prefetch_related(
            'customer', 'post', 'customer_frame').filter(
            is_downloaded=True, customer=customer, post__file_type=file_type
        )
        customer_other_post_frame_data = CustomerOtherPostFrameMapping.objects.prefetch_related(
            'customer', 'other_post', 'customer_frame').filter(
            is_downloaded=True, customer=customer, other_post__file_type=file_type
        )

        # Combine the filtered data from both models
        merged_queryset = customer_post_frame_data.union(customer_other_post_frame_data)

        return merged_queryset

    def get_serializer_class(self):
        if self.action == 'list':
            queryset = self.get_queryset()
            if queryset.model == CustomerPostFrameMapping:
                return serializers.CustomerPostFrameMappingSerializer
            elif queryset.model == CustomerOtherPostFrameMapping:
                return serializers.CustomerOtherPostFrameMappingSerializer

        return super().get_serializer_class()