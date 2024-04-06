from django.shortcuts import render

# Create your views here.
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from .serializers import (
    GoogleSignInSerializer,
    PhoneOTPRequestSerializer,
    OTPVerificationSerializer,
    EmailOTPRequestSerializer,
    CustomUserEmailSerializer
    # CustomUserPhoneSerializer,
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from .models import PendingUser
from datetime import datetime, timedelta
from django.conf import settings
from vendors.utilities import send_otp_email
from django.utils import timezone
from .utilities import send_otp, create_Mobile_user, generate_otp, create_email_user

# Create your views here.



class GoogleOauthSignInview(GenericAPIView):
    serializer_class=GoogleSignInSerializer

    def post(self, request):
        print(request.data)
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data=((serializer.validated_data)['access_token'])
        return Response(data, status=status.HTTP_200_OK) 



#email otp request view

class EmailOTPRequestView(APIView):
    def post(self, request):
        serializer = EmailOTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            if email:
                request.session['email'] = email
                username = email.split('@')[0] 
                otp = generate_otp()
                expiry_time = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
                pending_user = PendingUser.objects.create(email=email, otp=otp, expiry_time=expiry_time)
                try:
                    send_otp_email(email, username, otp)  # Send OTP to the provided email address
                    return Response({"detail": "OTP sent successfully"}, status=status.HTTP_200_OK)
                except Exception as e:
                    # If sending OTP fails, delete the pending user
                    pending_user.delete()
                    return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"error": "Email not provided"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

from django.utils import timezone

#email otp verification view

class OTPVerificationEmailView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data.get('otp')
            
            # Get email from session
            email = request.session.get('email')
            if not email:
                return Response({"error": "Email not found in session"}, status=status.HTTP_400_BAD_REQUEST)

            if otp:
                try:
                    pending_user = PendingUser.objects.get(email=email, otp=otp)
                    if pending_user.expiry_time >= timezone.now():
                        print(timezone.now())
                        # OTP is valid and not expired, login or create user
                        user = create_email_user(email, otp)
                        # Delete the pending user after successful verification
                        pending_user.delete()

                        # Generate JWT tokens
                        access_token = RefreshToken.for_user(user)
                        refresh_token = RefreshToken.for_user(user)
                        
                        # Set a long expiration time for the refresh token (e.g., 1 year)
                        refresh_token_exp = timezone.now() + timedelta(days=365)

                        # Serialize user data
                        user_serializer = CustomUserEmailSerializer(user)

                        return Response({
                            "access_token": str(access_token.access_token),
                            "refresh_token": str(refresh_token),
                            "refresh_token_expiry": refresh_token_exp.isoformat(),  # Serialize expiration time
                            "user": user_serializer.data,  # Include serialized user data
                            "message": "User logged in successfully",
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)
                except PendingUser.DoesNotExist:
                    return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#phone otp request view

class PhoneOTPRequestView(APIView):
    def post(self, request):
        serializer = PhoneOTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data.get('phone_number')
            if phone_number:
                request.session['phone_number'] = phone_number
                otp = generate_otp()
                expiry_time = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
                pending_user = PendingUser.objects.create(phone_number=phone_number, otp=otp, expiry_time=expiry_time)
                try:
                    send_otp(phone_number, otp)  # Send OTP to the provided phone number
                    return Response({"detail": "OTP sent successfully"}, status=status.HTTP_200_OK)
                except Exception as e:
                    # If sending OTP fails, delete the pending user
                    pending_user.delete()
                    return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"error": "Phone number not provided"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#phone otp verification view

class OTPVerificationView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data.get('otp')
            phone_number = request.session.get('phone_number')
            if otp and phone_number:
                try:
                    pending_user = PendingUser.objects.get(phone_number=phone_number, otp=otp)
                    if pending_user.expiry_time >= timezone.now():
                        # OTP is valid and not expired, login or create user
                        user = create_Mobile_user(phone_number, otp)
                        # Delete the pending user after successful verification
                        pending_user.delete()
                        
                        # Generate JWT tokens
                        access_token = RefreshToken.for_user(user)
                        refresh_token = RefreshToken.for_user(user)
                        
                        # Set a long expiration time for the refresh token (e.g., 1 year)
                        refresh_token_expiry = timezone.now() + timedelta(days=365)

                        # Serialize user data
                        # user_serializer = CustomUserPhoneSerializer(user)
                        user_data = {
                            "id": user.id,
                            "phone_number": user.phone_number,
                            # Add other user fields as needed
                        }

                        return Response({
                            "access_token": str(access_token.access_token),
                            "refresh_token": str(refresh_token),
                            "refresh_token_expiry": refresh_token_expiry.isoformat(), 
                            "user": user_data,  
                            "detail": "User logged in successfully",
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)
                except PendingUser.DoesNotExist:
                    return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Invalid OTP or phone number"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
