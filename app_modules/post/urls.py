from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)

router.register('category', views.CategoeryViewset, basename='category')
router.register('sub-categories-list', views.SubCategoryViewSet, basename='sub-category')
router.register('sub-categories', views.SubcategoryListViewSet, basename='sub-categories-list')
router.register('event', views.EventViewset, basename='event')
router.register('post', views.PostViewset, basename='post')
router.register('business-post', views.BusinessPostViewset, basename='business-post')
router.register('other-post', views.OtherPostViewset, basename='other-post')
router.register('customer-post-frame', views.CustomerPostFrameMappingViewSet, basename='customer-post-frame')
router.register('customer-other-post-frame', views.CustomerOtherPostFrameMappingViewSet, basename='customer-other-post-frame')
router.register('business-post-frame', views.BusinessPostFrameMappingViewSet, basename='business-post-frame')


urlpatterns = [
    path('', include(router.urls)),
    path('event-list', views.EventListApiView.as_view(), name='event-list'),
    path('category-list', views.CategoryListApiView.as_view(), name='category-list'),
    path('generate_output_video', views.generate_output_video, name='generate_output_video'),
    path('delete-past-events', views.DeletePastEventsView.as_view(), name='delete_past_events'),
]
