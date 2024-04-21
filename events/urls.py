from django.urls import path
from .views import (
    EventListAPIView,
    LocationListAPIView,
    EventByLocationAPIView,
    EventDetailAPIView,
    TicketTypeListAPIView,
    TicketBookingAPIView
)

urlpatterns = [
    path('locations/', LocationListAPIView.as_view(), name='location-list'),
    path('by_location/', EventByLocationAPIView.as_view(), name='events-by-location'),
    path('list_all_events/', EventListAPIView.as_view(), name='event-list'),
    path('event_details/<int:pk>/', EventDetailAPIView.as_view(), name='event-detail'),
    path('event/<int:event_id>/tickets/', TicketTypeListAPIView.as_view(), name='event_tickets'),
    path('book-tickets/<int:ticket_id>/', TicketBookingAPIView.as_view(), name='book-tickets'),

]