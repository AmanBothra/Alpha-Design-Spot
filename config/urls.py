
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Alpha Design Spot API",
      default_version='v1',
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

admin.site.site_title = "Alpha Design Spot"
admin.site.site_header = "Alpha Design Spot"
admin.site.index_title = "Site administration"


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('silk/', include('silk.urls', namespace='silk')),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path("__debug__/", include("debug_toolbar.urls")),
    # jwt
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # API Endpoints
    path("api/auth/", include("account.urls"), name="account"),
    path("api/master/", include("master.urls"), name="master"),
    path("api/post/", include("post.urls"), name="master"),
    path("api/website/", include("website.urls"), name="website"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:  
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
