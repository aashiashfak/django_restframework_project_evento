from django.urls import path
from .views import (
    EventListAPIView,
    LocationListAPIView,
    EventByLocationAPIView,
)

urlpatterns = [
    path('locations/', LocationListAPIView.as_view(), name='location-list'),
    path('by_location/', EventByLocationAPIView.as_view(), name='events-by-location'),
    path('listAllEvents/', EventListAPIView.as_view(), name='event-list'),
]