from django.urls import include, path
from rest_framework import routers
from app_modules.website import views

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'enquiry', views.EnquiryViewSet, basename='enquiry')
router.register(r'testimonail', views.TestimonalViewSet, basename='testimonal')


urlpatterns = [
    path('', include(router.urls)),
]