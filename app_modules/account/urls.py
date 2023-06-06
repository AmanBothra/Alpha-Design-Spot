from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)

router.register('customer-frame', views.CustomerFrameViewSet, basename="customer_frame")
router.register('user-profile', views.UserProfileListApiView, basename='user-profile-list')

urlpatterns = [
    path('', include(router.urls)),
    path('register', views.RegistrationView.as_view(), name='register'),
    path('login', views.LoginView.as_view(), name='register'),
]
