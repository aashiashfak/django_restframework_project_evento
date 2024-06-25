from django.urls import path
from .views import (
    EventListAPIView,
    LocationListAPIView,
    EventByLocationAPIView,
    EventDetailAPIView,
    TicketTypeListAPIView,
    TicketBookingAPIView,
    ConfirmPaymentAPIView,
    CancelTicketAPIView,
    HandleRazorpayWebhookView,
    TrendingEventAPIView,
    WishListAPIView,
    CategoryListAPIView
)

urlpatterns = [
    path('locations/', LocationListAPIView.as_view(), name='location-list'),
    path('by_location/<int:location_id>/', EventByLocationAPIView.as_view(), name='events-by-location'),
    path('list_all_events/', EventListAPIView.as_view(), name='event-list'),
    path('event_details/<int:pk>/', EventDetailAPIView.as_view(), name='event-details'),
    path('event/<int:event_id>/tickets/', TicketTypeListAPIView.as_view(), name='event_tickets'),
    path('book-tickets/<int:ticket_id>/', TicketBookingAPIView.as_view(), name='book-tickets'),
    path('confirm-payment/<int:ticket_id>/', ConfirmPaymentAPIView.as_view(), name='confirm-payment'),
    path('cancel-ticket/<int:ticket_id>/', CancelTicketAPIView.as_view(), name='cancel_ticket'),
    path('api/handle-razorpay-webhook/', HandleRazorpayWebhookView.as_view(), name='handle-razorpay-webhook'),
    path('trending-events/', TrendingEventAPIView.as_view(), name='trending-events'),
    path('wishlist/', WishListAPIView.as_view(), name='wishlist'),
    path('wishlist/<int:event_id>/', WishListAPIView.as_view(), name='wishlist-detail'),
    path('categories/', CategoryListAPIView.as_view(), name='categories'),



]