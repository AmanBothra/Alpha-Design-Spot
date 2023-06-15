from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)

router.register('category', views.CategoeryViewset, basename='category')
router.register('event', views.EventViewset, basename='event')
router.register('post', views.PostViewset, basename='post')
router.register('other-post', views.OtherPostViewset, basename='other-post')

urlpatterns = [
    path('', include(router.urls)),
]
