from .views import (
    GoogleOauthSignInview,
    PhoneOTPRequestView,
    OTPVerificationView,
    OTPVerificationEmailView,
    EmailOTPRequestView,
    ResendOTPView
)
from django.urls import path


urlpatterns = [
    path('google/oauth1/', GoogleOauthSignInview.as_view(), name='google-signin'),
    path('email-otp-request/', EmailOTPRequestView.as_view(), name='email-otp-request'),
    path('email-otp-verification/',  OTPVerificationEmailView.as_view(), name='email-otp-verification'),
    path('phone-otp-request/', PhoneOTPRequestView.as_view(), name='phone-otp-request'),
    path('phone-otp-verification/', OTPVerificationView.as_view(), name='phone-otp-verification'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),


]