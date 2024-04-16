
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import permissions


def send_otp_email(email, contact_name, otp):
    subject = "Your OTP for Verification"
    message = f"Hi {contact_name},\n\nYour OTP is: {otp}\n\nPlease use this OTP to complete your Verification process.\n\nThank you."
    sender = settings.EMAIL_HOST_USER  # Sender's email address
    recipient_list = [email]
    send_mail(subject, message, sender, recipient_list)




class IsVendor(permissions.BasePermission):
    """
    Custom permission to check if the user is a vendor.
    """
    def has_permission(self, request, view):
        """
        Check if the user is a vendor.
        """
        return request.user.is_vendor


from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Vendor  # Import your Vendor model

class CustomVendorJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        user = super().authenticate(request)
        
        if user is not None:
            try:
                vendor = Vendor.objects.get(user=user[0])
                setattr(request, 'vendor', vendor)
            except Vendor.DoesNotExist:
                setattr(request, 'vendor', None)
                
        return user
