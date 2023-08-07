from datetime import date, timedelta
from rest_framework.views import APIView
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from app_modules.post import serializers
from app_modules.post.models import Category, Event, Post, OtherPost, CustomerPostFrameMapping, \
    CustomerOtherPostFrameMapping
from lib.helpers import generate_video_with_frame
from lib.viewsets import BaseModelViewSet
from .filters import EventFilter


class CategoeryViewset(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'name': ["in", "exact"]
    }

    def get_queryset(self):
        file_type = self.request.GET.get('file_type')

        queryset = super().get_queryset()
        exclude_main_categories = self.request.query_params.get('exclude_main_categories', True)  # set by default true

        if exclude_main_categories:
            queryset = queryset.exclude(sub_category__isnull=False)

        if file_type:
            queryset = Category.objects.filter(other_post_categories__file_type=file_type).distinct()
        return queryset

    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        category = self.get_object()
        subcategories = Category.objects.filter(sub_category=category)
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)


class SubcategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(sub_category__isnull=False)
    serializer_class = serializers.SubcategorySerializer
    pagination_class = None


class EventViewset(BaseModelViewSet):
    # queryset = Event.objects.all()
    serializer_class = serializers.EventSerializer
    filterset_class = EventFilter
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ('event_date', 'name')

    def get_queryset(self):
        date_type = self.request.GET.get('date_type')
        file_type = self.request.GET.get('file_type')

        today = date.today()
        tomorrow = today + timedelta(days=1)
        queryset = Event.objects.all().order_by('-event_date')

        if date_type == "today":
            queryset = queryset.filter(event_date=today)
        elif date_type == "tomorrow":
            queryset = queryset.filter(event_date=tomorrow)
        elif date_type == "upcoming":
            queryset = queryset.filter(event_date__gt=tomorrow).order_by("event_date")

        if file_type:
            queryset = queryset.filter(post_event__file_type=file_type).distinct()
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
                raise ValidationError({"event": "A post with the same event and group already exists."})

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


class EventListApiView(ListAPIView):
    pagination_class = None
    serializer_class = serializers.EventSerializer
    queryset = Event.objects.all()


class CategoryListApiView(ListAPIView):
    pagination_class = None
    serializer_class = serializers.CategorySerializer
    queryset = Category.objects.select_related('sub_category').all()


@api_view(['POST'])
def generate_output_video(request):
    # Get the customer_post_id from the request data
    customer = request.user
    customer_post_id = request.data.get("customer_post_id")
    event_id = request.data.get("event_id")
    customer_other_post_id = request.data.get("customer_other_post_id")
    categoery_id = request.query_params.get('categoery_id')

    if customer_post_id:
        try:
            data = CustomerPostFrameMapping.objects.get(id=customer_post_id)
        except CustomerPostFrameMapping.DoesNotExist:
            return Response({"message": "Invalid customer post mapping ID."}, status=400)

    if customer_other_post_id:
        try:
            data = CustomerOtherPostFrameMapping.objects.get(id=customer_other_post_id)
        except CustomerOtherPostFrameMapping.DoesNotExist:
            return Response({"message": "Invalid customer other-post mapping ID."}, status=400)

    if event_id:
        try:
            data = CustomerPostFrameMapping.objects.get(customer=customer, post__event=event_id)
        except CustomerPostFrameMapping.DoesNotExist:
            return Response({"message": "Invalid event ID."}, status=400)

    if categoery_id:
        try:
            data = CustomerPostFrameMapping.objects.get(customer=customer, other_post__category=categoery_id)
        except CustomerPostFrameMapping.DoesNotExist:
            return Response({"message": "Invalid category ID."}, status=400, request=request)

    # Extract the related CustomerFrame and Post objects from the mapping object
    customer_frame = data.customer_frame
    post = data.post

    # Check if the output video URL is already cached for this user and request data
    cache_key = f"user_{customer.id}_post_{customer_post_id}_event_{event_id}_category_{categoery_id}"
    output_video_url = cache.get(cache_key)

    if not output_video_url:
        print("yes video hai ")
        # If the output video URL is not cached, generate the video with the frame
        output_video_url = generate_video_with_frame(customer_frame, post)

        # Cache the output video URL for a certain duration (e.g., 1 day)
        cache.set(cache_key, output_video_url, timeout=86400)

    # Generate the video with the frame overlay using the separate function
    output_video_url = generate_video_with_frame(customer_frame, post)

    return Response({"message": "Video processing completed.", "output_video": output_video_url}, status=200)


class DeletePastEventsView(APIView):
    def delete(self, request):
        today = date.today()
        events_to_delete = Event.objects.filter(event_date__lt=today)
        events_to_delete.delete()
        return Response(
            {'message': 'Successfully deleted past events.'},
        )
