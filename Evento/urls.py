from django.conf import settings
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
# from django.views.generic import TemplateView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.contrib.staticfiles.urls import staticfiles_urlpatterns



schema_view = get_schema_view(
    openapi.Info(
        title="Author_Book_DRF_API_doc",
        default_version='v1',
        description="Guide for the REST API",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


    



urlpatterns = [
    path('api_schema/', schema_view.without_ui(cache_timeout=0), name='api_schema'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('vendors/', include('vendors.urls')),
    path('superuser/', include('customadmin.urls')),
    path('events/', include('events.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

       
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar
    urlpatterns+= path("__debug__/", include("debug_toolbar.urls")),
