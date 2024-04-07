from django.urls import path
from .views import (
    VendorSignupView,
    VendorVerifyOtpView,
    VendorLoginView 
)

urlpatterns = [
    path('vendor/signup/', VendorSignupView.as_view(), name='vendor_signup'),
    path('vendor/verify-otp/', VendorVerifyOtpView.as_view(), name='verify_otp'),
    path('vendor/login/', VendorLoginView.as_view(), name='vendor_login'),
]
