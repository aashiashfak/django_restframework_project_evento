from rest_framework import generics, status
from rest_framework.response import Response
from .models import Vendor
from .serializers import (
    VendorSignupSerializer,
    VendorSerializer,
    VendorLoginSerializer
)
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from accounts.serializers import OTPVerificationSerializer
from accounts.models import PendingUser
from django.conf import settings
from accounts.utilities import generate_otp
from .utilities import send_otp_email
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate


class VendorSignupView(APIView):
    def post(self, request):
        serializer = VendorSignupSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = generate_otp()
            expiry_time = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
            pending_user, created = PendingUser.objects.update_or_create(
                    email=email,
                    defaults={'otp': otp, 'expiry_time': expiry_time}
                )
            contact_name=serializer.validated_data['contact_name']
            try:
                send_otp_email(email, contact_name, otp)
                request.session['vendor_signup_data'] = serializer.validated_data
                return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
            except Exception as e:
                pending_user.delete()
                return Response({'error': 'Failed to send OTP. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class VendorVerifyOtpView(APIView):
    def post(self, request):
        try:
            email = request.session['vendor_signup_data']['email']
        except KeyError:
            return Response({'error': 'Email not found in session'}, status=status.HTTP_400_BAD_REQUEST)
        
        otp_serializer = OTPVerificationSerializer(data=request.data)
        if otp_serializer.is_valid():
            otp = otp_serializer.validated_data['otp']
            if email:
                try:
                    pending_user = PendingUser.objects.get(email=email, otp=otp)
                    # Check if OTP is expired
                    if pending_user.expiry_time < timezone.now():
                        pending_user.delete()
                        return Response({'error': 'OTP expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

                    vendor_data = request.session.get('vendor_signup_data')
                    vendor_data.pop('confirm_password')  
                    password = vendor_data.pop('password')
                    hashed_password = make_password(password)
                    vendor = Vendor.objects.create(**vendor_data, password=hashed_password, is_vendor=True, is_active=True) 
                    vendor.save()
                    access_token = RefreshToken.for_user(vendor)
                    refresh_token = RefreshToken.for_user(vendor)
                    refresh_token_exp = timezone.now() + timedelta(days=365)
                    pending_user.delete()
                    vendor_serializer = VendorSerializer(vendor)
                    return Response({
                        'vendor': vendor_serializer.data,
                        'access_token': str(access_token),
                        'refresh_token': str(refresh_token),
                        "refresh_token_expiry": refresh_token_exp.isoformat(),  
                    }, status=status.HTTP_200_OK)
                except PendingUser.DoesNotExist:
                    return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(otp_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'No pending user found'}, status=status.HTTP_400_BAD_REQUEST)


class VendorLoginView(APIView):
    def post(self, request):
        serializer = VendorLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
