from django.conf import settings
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

# from rest_framework.routers import DefaultRouter
# from events.views import VendorEventViewSet


# router = DefaultRouter()
# router.register(r'events', VendorEventViewSet)


    



urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('vendors/', include('vendors.urls')),
    path('superuser/', include('customadmin.urls')),
    path('events/', include('events.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('Allevents/', include(router.urls)),

       
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns+= path("__debug__/", include("debug_toolbar.urls")),
