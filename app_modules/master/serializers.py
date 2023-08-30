from rest_framework import serializers

from app_modules.master.models import (
    Banner, BirthdayPost, SplashScreen, Tutorials, About, PrivacyPolicy, TermsAndCondition, Feedback,
)


class BannerSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = Banner
        fields = "__all__"


class BirthdayPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BirthdayPost
        fields = "__all__"


class SplashScreenSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplashScreen
        fields = "__all__"


class TutorialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutorials
        fields = "__all__"


class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = About
        fields = "__all__"


class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = "__all__"


class TermsAndConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsAndCondition
        fields = "__all__"


class FeedbackSerializer(serializers.ModelSerializer):
    customer_detail = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Feedback
        fields = ['id', 'feedback', 'customer_detail', 'added_on']
        
    def get_customer_detail(self, obj):
        return {
            "number": obj.customer.whatsapp_number,
            "name": f"{obj.customer.first_name} {obj.customer.last_name}",
        }