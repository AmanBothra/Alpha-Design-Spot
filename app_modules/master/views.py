from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework import status, permissions

from app_modules.master import serializers
from app_modules.master.models import (
    Banner, BirthdayPost, SplashScreen, Tutorials, About, PrivacyPolicy, TermsAndCondition, Feedback
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

    