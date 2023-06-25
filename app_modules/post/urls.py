from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)

router.register('category', views.CategoeryViewset, basename='category')
router.register('sub-categories', views.SubcategoryViewSet, basename='sub-category')
router.register('event', views.EventViewset, basename='event')
router.register('post', views.PostViewset, basename='post')
router.register('other-post', views.OtherPostViewset, basename='other-post')
router.register('customer-post-frame', views.CustomerPostFrameMappingViewSet, basename='customer-post-frame')
router.register('customer-other-post-frame', views.CustomerOtherPostFrameMappingViewSet, basename='customer-other-post-frame')
router.register('my-post', views.DownloadedDataViewSet, basename='my-post')


urlpatterns = [
    path('', include(router.urls)),
]
