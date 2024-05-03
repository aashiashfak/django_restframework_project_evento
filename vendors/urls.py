from django.urls import path
from .views import (
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
    TicketTypeDetailUpdateAPIView,
    VendorDashboardAPIView,
    VendorBookedUsersAPIView,
    TicketCountGraphAPIView
)


urlpatterns = [
    path('vendor/signup/', VendorSignupView.as_view(), name='vendor_signup'),
    path('vendor/verify-otp/', VendorVerifyOtpView.as_view(), name='verify_otp'),
    path('vendor/login/', VendorLoginView.as_view(), name='vendor_login'),
    path('vendor/forget-password/', VendorForgetPasswordOTPsent.as_view(), name='forget_password'),
    path('vendor/verify-fortget-otp/', VerifyOTPView.as_view(), name='forget_Pass_verify_otp'),
    path('vendor/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('vendor/profile/', VendorProfileAPIView.as_view(), name='vendor-profile'),
    path('vendor/create_event/', CreateEventView.as_view(), name='create_event'),
    path('vendor/events/<int:event_id>/', VendorEventDetailView.as_view(), name='vendor_event_detail'),
    path('vendor/ticket-types/', TicketTypeListCreateAPIView.as_view(), name='ticket_type_list_create'),
    path('vendor/ticket-types/<int:pk>/', TicketTypeDetailUpdateAPIView.as_view(), name='ticket_type_detail_update'),
    path('vendor/dashboard/', VendorDashboardAPIView.as_view(), name='vendor_dashboard'),
    path('vendor/user-ticket-details/', VendorBookedUsersAPIView.as_view(), name='user_ticket_details'),
     path('vendor/ticket-count-graph/', TicketCountGraphAPIView.as_view(), name='ticket_count_graph'),
]
