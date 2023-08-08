from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter

from app_modules.master import serializers
from app_modules.master.models import (
    Banner, BirthdayPost, SplashScreen, Tutorials, About, PrivacyPolicy, TermsAndCondition, Feedback,
    BusinessCategory
)
from lib.viewsets import BaseModelViewSet


class BannerViewSet(BaseModelViewSet):
    serializer_class = serializers.BannerSerializer
    queryset = Banner.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']


class BirthdayPostViewSet(BaseModelViewSet):
    serializer_class = serializers.BirthdayPostSerializer
    queryset = BirthdayPost.objects.all()
    http_method_names = ['get', 'post', 'patch']
    
    def create(self, request, *args, **kwargs):
        # Check if an object already exists
        if BirthdayPost.objects.exists():
            return Response(
                {'image': 'A birthday post already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)


class SplashScreenViewSet(BaseModelViewSet):
    serializer_class = serializers.SplashScreenSerializer
    queryset = SplashScreen.objects.all()
    http_method_names = ['get', 'post', 'patch']
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        # Check if an object already exists
        if SplashScreen.objects.exists():
            return Response(
                {'file': 'A splash screen already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)


class TutorialsViewSet(BaseModelViewSet):
    serializer_class = serializers.TutorialsSerializer
    queryset = Tutorials.objects.all()


class AboutViewSet(BaseModelViewSet):
    serializer_class = serializers.AboutSerializer
    queryset = About.objects.all()


class PrivacyPolicyViewSet(BaseModelViewSet):
    serializer_class = serializers.PrivacyPolicySerializer
    queryset = PrivacyPolicy.objects.all()


class TermsAndConditionViewSet(BaseModelViewSet):
    serializer_class = serializers.TermsAndConditionSerializer
    queryset = TermsAndCondition.objects.all()


class FeedbackViewSet(BaseModelViewSet):
    serializer_class = serializers.FeedbackSerializer
    queryset = Feedback.objects.all()
    http_method_names = ['get', 'post']
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class BusinessCategoeryViewset(BaseModelViewSet):
    serializer_class = serializers.BusinessCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'name': ["in", "exact"]
    }
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = BusinessCategory.objects.filter(sub_category__isnull=True)
        return queryset

    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        category = self.get_object()
        subcategories = BusinessCategory.objects.filter(sub_category=category)
        
        category_name = self.request.query_params.get('category_name')
        if category_name:
            subcategories = subcategories.filter(name__icontains=category_name)
        
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)
    
    
    @action(detail=True, methods=['patch'])
    def update_subcategory(self, request, pk=None):
        print(request.data)
        sub_category = self.get_object()
        serializer = self.get_serializer(sub_category, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)