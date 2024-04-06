from django.urls import path
from .views import VendorSignUpView, VerifyOTPView


urlpatterns = [
    path('vendor/signup/', VendorSignUpView.as_view(), name='vendor_signup'),
    path('vendor/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
]
