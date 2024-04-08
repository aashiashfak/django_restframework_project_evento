from django.urls import path
from .views import (
    VendorSignupView,
    VendorVerifyOtpView,
    VendorLoginView,
    VendorForgetPasswordOTPsent,
    VerifyOTPView,
    ChangePasswordView
)

urlpatterns = [
    path('vendor/signup/', VendorSignupView.as_view(), name='vendor_signup'),
    path('vendor/verify-otp/', VendorVerifyOtpView.as_view(), name='verify_otp'),
    path('vendor/login/', VendorLoginView.as_view(), name='vendor_login'),
    path('vendor/forget-password/', VendorForgetPasswordOTPsent.as_view(), name='forget_password'),
    path('vendor/verify-fortget-otp/', VerifyOTPView.as_view(), name='forget_Pass_verify_otp'),
    path('vendor/change-password/', ChangePasswordView.as_view(), name='change_password')
]
