from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)

router.register('category', views.CategoeryViewset, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
