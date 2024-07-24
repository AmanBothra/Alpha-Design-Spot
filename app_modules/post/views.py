from datetime import date, timedelta

from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from app_modules.post import serializers
from app_modules.post.models import Category, Event, Post, OtherPost, CustomerPostFrameMapping, \
    CustomerOtherPostFrameMapping, BusinessPost, BusinessPostFrameMapping, BusinessCategory
from lib.helpers import generate_video_with_frame
from lib.viewsets import BaseModelViewSet
from .filters import EventFilter, BusinessPostFilter, BusinessCategoryFilter


class CategoryView(BaseModelViewSet):
    serializer_class = serializers.CategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'name': ["in", "exact"]
    }

    def get_queryset(self):
        file_type = self.request.GET.get('file_type')

        queryset = Category.objects.filter(sub_category__isnull=True).order_by('-id')
        exclude_main_categories = self.request.query_params.get('exclude_main_categories')

        if exclude_main_categories == "false":
            queryset = Category.objects.filter(sub_category__isnull=False).order_by('-id')

        if file_type:
            queryset = Category.objects.filter(other_post_categories__file_type=file_type).distinct()
        return queryset

    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        category = self.get_object()
        subcategories = Category.objects.filter(sub_category=category)
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path='delete-subcategory/(?P<subcategory_id>[0-9]+)')
    def delete_subcategory(self, request, subcategory_id=None):
        try:
            subcategory = Category.objects.get(pk=subcategory_id, sub_category__isnull=False)
            subcategory.delete()
            return Response({"success": True, "message": "Subcategory deleted successfully"},
                            status=status.HTTP_204_NO_CONTENT)
        except Category.DoesNotExist:
            return Response({"success": False, "message": "Subcategory not found"}, status=status.HTTP_404_NOT_FOUND)


class SubcategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(sub_category__isnull=False).order_by('-id')
    serializer_class = serializers.SubcategorySerializer
    pagination_class = None


class BusinessCategoeryViewset(BaseModelViewSet):
    queryset = BusinessCategory.objects.all().order_by('-id')
    serializer_class = serializers.BusinessCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ('name', 'profession_type')
    filterset_class = BusinessCategoryFilter


class BusinessCategoryList(viewsets.ReadOnlyModelViewSet):
    queryset = BusinessCategory.objects.all().order_by('-id')
    serializer_class = serializers.BusinessCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ('name', 'profession_type')
    pagination_class = None


class EventViewset(BaseModelViewSet):
    # queryset = Event.objects.all()
    serializer_class = serializers.EventSerializer
    filterset_class = EventFilter
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ('event_date', 'name', 'event_type')

    def get_queryset(self):
        date_type = self.request.GET.get('date_type')

        today = date.today()
        tomorrow = today + timedelta(days=1)
        five_days_from_today = today + timedelta(days=5)

        queryset = Event.objects.all().order_by('event_date')

        if date_type == "today":
            queryset = queryset.filter(event_date=today)
        elif date_type == "tomorrow":
            queryset = queryset.filter(event_date=tomorrow).order_by('-id')
        elif date_type == "upcoming":
            queryset = queryset.filter(
                event_date__gt=tomorrow,
                event_date__lte=five_days_from_today
            ).order_by("event_date")

        return queryset


class PostViewset(BaseModelViewSet):
    queryset = Post.objects.select_related('event', 'group').all().order_by('-id')
    serializer_class = serializers.PostSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['group__name', 'event__name', 'file_type', 'event__event_date']

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

        response = super().create(request, *args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            group_name = None
            if group_id:
                group_name = Post.objects.get(id=response.data['id']).group.name

            modified_data = response.data.copy()
            if group_name:
                modified_data["message"] = f"The Post for group '{group_name}' has been created successfully"
            else:
                modified_data["message"] = "The Post has been created successfully"

            response.data = modified_data

        return response


class OtherPostViewset(BaseModelViewSet):
    queryset = OtherPost.objects.select_related('category', 'group').all().order_by('-id')
    serializer_class = serializers.OtherPostSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['group__name', 'category__name', 'file_type']


class BusinessPostViewset(BaseModelViewSet):
    serializer_class = serializers.BusinessPostSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        'group__name', 'file_type', 'business_category__name', 'profession_type'
    ]
    filterset_class = BusinessPostFilter

    def get_queryset(self):
        file_type = self.request.query_params.get('file_type')
        queryset = BusinessPost.objects.select_related('business_category', 'group').all()

        if file_type in ["image", "video"]:
            queryset = queryset.filter(file_type=file_type)

        return queryset

    def get_serializer_context(self):
        context = super(BusinessPostViewset, self).get_serializer_context()
        return context


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
            queryset = queryset.filter(customer=customer, other_post__category=categoery_id)

        return queryset


class BusinessPostFrameMappingViewSet(BaseModelViewSet):
    queryset = BusinessPostFrameMapping.objects
    serializer_class = serializers.BusinessPostFrameMappingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_downloaded']
    http_method_names = ['get', 'patch']

    def get_serializer_context(self):
        context = super(BusinessPostFrameMappingViewSet, self).get_serializer_context()
        context["user"] = self.request.user
        return context

    def get_queryset(self):
        customer = self.request.user
        business_post_id = self.request.query_params.get('business_post_id')

        queryset = self.queryset.prefetch_related('customer', 'post', 'customer_frame')
        if business_post_id:
            queryset = queryset.filter(customer=customer)

        return queryset


class EventListApiView(ListAPIView):
    pagination_class = None
    serializer_class = serializers.EventSerializer

    def get_queryset(self):
        event_type = self.request.query_params.get('event_type', None)

        today = date.today()
        queryset = Event.objects.filter(event_date__gte=today).order_by('-id')

        if event_type == 'image':
            queryset = queryset.filter(event_type='image')

        if event_type == 'video':
            queryset = queryset.filter(event_type='video')

        return queryset


class CategoryListApiView(ListAPIView):
    pagination_class = None
    serializer_class = serializers.CategorySerializer
    queryset = Category.objects.select_related('sub_category').all().order_by('-id')


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

        for event in events_to_delete:
            posts_to_delete = Post.objects.filter(event=event)

            for post in posts_to_delete:
                mappings_to_delete = CustomerPostFrameMapping.objects.filter(post=post)
                mappings_to_delete.delete()

            posts_to_delete.delete()

        events_to_delete.delete()

        return Response(
            {'message': 'Successfully deleted past events.'},
        )
