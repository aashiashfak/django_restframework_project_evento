
from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(email, contact_name, otp):
    subject = "Your OTP for Vendor Sign Up"
    message = f"Hi {contact_name},\n\nYour OTP is: {otp}\n\nPlease use this OTP to complete your sign up process.\n\nThank you."
    sender = settings.EMAIL_HOST_USER  # Sender's email address
    recipient_list = [email]
    send_mail(subject, message, sender, recipient_list)

