from django.conf import settings
from django.contrib import admin
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from events.views import VendorEventViewSet


router = DefaultRouter()
router.register(r'events', VendorEventViewSet)


    



urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('vendors/', include('vendors.urls')),
    path('superuser/', include('customadmin.urls')),
    path('Allevents/', include(router.urls)),
       
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns+= path("__debug__/", include("debug_toolbar.urls")),
