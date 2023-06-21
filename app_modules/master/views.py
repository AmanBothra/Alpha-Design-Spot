from django_filters.rest_framework import DjangoFilterBackend

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


class SplashScreenViewSet(BaseModelViewSet):
    serializer_class = serializers.SplashScreenSerializer
    queryset = SplashScreen.objects.all()


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

    