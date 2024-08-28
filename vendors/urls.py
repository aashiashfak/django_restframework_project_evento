from django.urls import path
from .views import (
    VendorReportGeneratorView,
    VendorSignupView,
    VendorVerifyOtpView,
    VendorLoginView,
    VendorForgetPasswordOTPsent,
    VerifyOTPView,
    ChangePasswordView,
    VendorProfileAPIView,
    CreateEventView,
    VendorEventDetailView,
    TicketTypeListCreateAPIView,
    TicketTypeRetrieveUpdateDestroyAPIView,
    VendorDashboardAPIView,
    VendorBookedTicketsAPIView,
    VendorTicketBookingDataView,
)


urlpatterns = [
    path('signup/', VendorSignupView.as_view(), name='vendor_signup'),
    path('vendor/verify-otp/', VendorVerifyOtpView.as_view(), name='verify_otp'),
    path('vendor/login/', VendorLoginView.as_view(), name='vendor_login'),
    path('vendor/forget-password/', VendorForgetPasswordOTPsent.as_view(), name='forget_password'),
    path('vendor/verify-fortget-otp/', VerifyOTPView.as_view(), name='forget_Pass_verify_otp'),
    path('vendor/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('vendor/profile/', VendorProfileAPIView.as_view(), name='vendor-profile'),
    path('vendor/get-create-event', CreateEventView.as_view(), name='create_event'),
    path('vendor/event/<int:event_id>/', VendorEventDetailView.as_view(), name='vendor_event_detail'),
    path('vendor/events/<int:event_id>/ticket-types/', TicketTypeListCreateAPIView.as_view(), name='ticket-types-list-create'),
    path('vendor/events/<int:event_id>/ticket-types/<int:id>/', TicketTypeRetrieveUpdateDestroyAPIView.as_view(), name='ticket-type-detail'),    path('vendor/dashboard/', VendorDashboardAPIView.as_view(), name='vendor_dashboard'),
    path('vendor/booked-ticket-details/', VendorBookedTicketsAPIView.as_view(), name='user_ticket_details'),
    path('vendor/ticket-booking-data/<str:date>/', VendorTicketBookingDataView.as_view(), name='ticket_count_graph'),
    path('vendor/report/<str:date>/', VendorReportGeneratorView.as_view(), name='vendor-ticket-report'),
]
