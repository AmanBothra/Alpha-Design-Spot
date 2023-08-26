from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)

router.register('customer-frame', views.CustomerFrameViewSet, basename="customer_frame")
router.register('user-profile', views.UserProfileListApiView, basename='user-profile-list')
router.register('customer-group', views.CustomerGroupViewSet, basename='customer-group')
router.register('customer-subscription', views.SubscriptionViewSet, basename='customer-subscription')
router.register('subscription-plan', views.PlanViewSet, basename='subscription-plan')
router.register('payment-method', views.PaymentMethodViewSet, basename='payment-method')



urlpatterns = [
    path('', include(router.urls)),
    path('register', views.RegistrationView.as_view(), name='register'),
    path('login', views.LoginView.as_view(), name='register'),
    path('customer-group-list', views.CustomerGroupListApiView.as_view(), name='customer-group-list'),
    path('customer-frame-list', views.CustomerFrameListApiView.as_view(), name='customer-frame-list'),
    path('customer-list', views.CustomerListApiView.as_view(), name='customer-list'),
    path('dashboard', views.DashboardApi.as_view(), name='dashboard-api'),
    path('check-email', views.CheckEmailExistence.as_view(), name='check-email'),
    path('send-otp', views.SendOTP.as_view(), name='send-otp'),
    path('verify-otp', views.VerifyOTP.as_view(), name='verify-otp'),
    path('new-password', views.SetNewPassword.as_view(), name='new-password'),
    
    
]
