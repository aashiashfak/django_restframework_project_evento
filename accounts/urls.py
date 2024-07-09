from .views import (
    GoogleOauthSignInview,
    PhoneOTPRequestView,
    OTPVerificationView,
    OTPVerificationEmailView,
    EmailOTPRequestView,
    ResendOTPView,
    UserProfileAPIView,
    UpdateEmailAPIView,
    VerifyUpdateEmailOTPView,
    UpdatePhoneAPIView,
    VerifyUpdatePhoneOTPView,
    FollowUnfollowVendorView,
    VendorFollowStatusView,
)
from django.urls import path


urlpatterns = [
    path('google/oauth1/', GoogleOauthSignInview.as_view(), name='google-signin'),
    path('email-otp-request/', EmailOTPRequestView.as_view(), name='email-otp-request'),
    path('email-otp-verification/',  OTPVerificationEmailView.as_view(), name='email-otp-verification'),
    path('phone-otp-request/', PhoneOTPRequestView.as_view(), name='phone-otp-request'),
    path('phone-otp-verification/', OTPVerificationView.as_view(), name='phone-otp-verification'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('user-profile/', UserProfileAPIView.as_view(), name='user-profile'),
    path('update-email/', UpdateEmailAPIView.as_view(), name='update-email'),
    path('verify-update-email-otp/', VerifyUpdateEmailOTPView.as_view(), name='verify-email-update-otp'),
    path('update-phone/', UpdatePhoneAPIView.as_view(), name='update-phone'),
    path('verify-update-phone-otp/', VerifyUpdatePhoneOTPView.as_view(), name='verify-phone-update-otp'),
    path('follow-unfollow/<int:vendor_id>/',FollowUnfollowVendorView.as_view(), name='follow-unfollow'),
    path('vendors/<int:vendor_id>/follow-status/', VendorFollowStatusView.as_view(), name='vendor-follow-status'),
    

    
]