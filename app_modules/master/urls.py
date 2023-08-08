from django.urls import include, path
from rest_framework import routers
from app_modules.master import views

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'banner', views.BannerViewSet, basename='banner')
router.register(r'birthday-post', views.BirthdayPostViewSet, basename='birthday-post')
router.register(r'splash-screen', views.SplashScreenViewSet, basename='splash-screen')
router.register(r'tutorial', views.TutorialsViewSet, basename='tutorial')
router.register(r'about', views.AboutViewSet, basename='about')
router.register(r'privacy-policy', views.PrivacyPolicyViewSet, basename='privacy-policy')
router.register(r'terms-and-condition', views.TermsAndConditionViewSet, basename='terms-and-condition')
router.register(r'feedback', views.FeedbackViewSet, basename='feedback')
router.register('business-category', views.BusinessCategoeryViewset, basename='business-category')

urlpatterns = [
    # Your existing URL patterns
    path('', include(router.urls)),
]
