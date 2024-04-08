from django.shortcuts import render
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
from rest_framework import status, permissions
from .models import PendingUser
from datetime import timedelta
from django.conf import settings
from vendors.utilities import send_otp_email
from django.utils import timezone
from .utilities import (
    send_otp,
    create_Mobile_user,
    generate_otp,
    create_email_user
)

# Create your views here.



class GoogleOauthSignInview(GenericAPIView):
    """
    Google OAuth sign-in view.
    """
    serializer_class=GoogleSignInSerializer

    def post(self, request):
        """
        Handle Google OAuth sign-in.
        Returns Response object containing the access token.
        """
        print(request.data)
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data=((serializer.validated_data)['access_token'])
        return Response(data, status=status.HTTP_200_OK) 



#email otp request view

class EmailOTPRequestView(APIView):
    """
    Email OTP request view.
    """
    def post(self, request):
        """
        Handle email OTP request.
        generates OTP and sent to user Email
        Returns Response object containing the result of the OTP request.
        """
        serializer = EmailOTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            if email:
                request.session['email'] = email
                username = email.split('@')[0] 
                otp = generate_otp()
                expiry_time = timezone.now() + timedelta(
                    minutes=settings.OTP_EXPIRY_MINUTES
                )
                pending_user, created = PendingUser.objects.update_or_create(
                    email=email,
                    defaults={'otp': otp, 'expiry_time': expiry_time}
                )
                try:
                    send_otp_email(email, username, otp)  
                    return Response(
                        {"detail": "OTP sent successfully"},
                        status=status.HTTP_200_OK
                    )
                except Exception as e:
                    pending_user.delete()
                    return Response(
                        {"error": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return Response(
                    {"error": "Email not provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class OTPVerificationEmailView(APIView):
    """
    Email OTP verification view.
    """
    def post(self, request):
        """
        Handle email OTP verification.
        Checks the user email from session and otp from Pending_users
        for verification.
        Returns object containing the result of the OTP verification.
        """
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data.get('otp')
            email = request.session.get('email')
            if not email:
                return Response(
                    {"error": "Email not found in session"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if otp:
                try:
                    pending_user = PendingUser.objects.get(email=email, otp=otp)
                    if pending_user.expiry_time >= timezone.now():
                        print(timezone.now())

                        user = create_email_user(email, otp)
                        pending_user.delete()

                        access_token = RefreshToken.for_user(user)
                        refresh_token = RefreshToken.for_user(user)
                        
                        refresh_token_exp = timezone.now() + timedelta(days=365)

                        user_serializer = CustomUserEmailSerializer(user)

                        return Response({
                            "access_token": str(access_token.access_token),
                            "refresh_token": str(refresh_token),
                            "refresh_token_expiry": refresh_token_exp.isoformat(),  
                            "user": user_serializer.data,  
                            "message": "User logged in successfully",
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response(
                            {"error": "OTP has expired"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except PendingUser.DoesNotExist:
                    return Response(
                        {"error": "Invalid OTP"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"error": "Invalid OTP"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

#phone otp request view

class PhoneOTPRequestView(APIView):
    """
    Phone OTP request view.
    """
    def post(self, request):
        """
        Handle phone OTP request.
        generates OTP and sent to user phone_number
        Returns Response object containing the result of the OTP request.
        """
        serializer = PhoneOTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data.get('phone_number')
            if phone_number:
                request.session['phone_number'] = phone_number
                otp = generate_otp()
                expiry_time = timezone.now() + timedelta(
                    minutes=settings.OTP_EXPIRY_MINUTES
                )
                pending_user, created = PendingUser.objects.update_or_create(
                    phone_number=phone_number,
                    defaults={'otp': otp, 'expiry_time': expiry_time}
                )
                try:
                    send_otp(phone_number, otp)  
                    return Response(
                        {"detail": "OTP sent successfully"},
                        status=status.HTTP_200_OK
                    )
                except Exception as e:
                    pending_user.delete()
                    return Response(
                        {"error": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return Response(
                    {"error": "Phone number not provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#phone otp verification view

class OTPVerificationView(APIView):
    """
    Phone OTP verification view.
    """

    def post(self, request):
        """
        Handle phone OTP verification.
        Checks the user phone_number from session and otp from Pending_users
        for verification.
        Returns Response object containing the result of the OTP verification.
        """
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data.get('otp')
            phone_number = request.session.get('phone_number')
            if otp and phone_number:
                try:
                    pending_user = PendingUser.objects.get(
                        phone_number=phone_number,
                        otp=otp
                    )
                    if pending_user.expiry_time >= timezone.now():

                        user = create_Mobile_user(phone_number, otp)

                        pending_user.delete()
                        
                        access_token = RefreshToken.for_user(user)
                        refresh_token = RefreshToken.for_user(user)
                        
                        refresh_token_expiry = timezone.now() + timedelta(days=365)

                        user_data = {
                            "id": user.id,
                            "phone_number": user.phone_number,
                        }

                        return Response({
                            "access_token": str(access_token.access_token),
                            "refresh_token": str(refresh_token),
                            "refresh_token_expiry": refresh_token_expiry.isoformat(), 
                            "user": user_data,  
                            "detail": "User logged in successfully",
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response(
                            {"error": "OTP has expired"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except PendingUser.DoesNotExist:
                    return Response(
                        {"error": "Invalid OTP"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"error": "Invalid OTP or phone number"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    """
    Resend OTP view.
    """
    def post(self, request):
        """
        Handle OTP resend request.
        Resends OTP to the user if the expiry time has passed.
        Response object containing the result of OTP resend operation.
        """
        try:
            email = request.session.get('email')
            phone_number = request.session.get('phone_number')

            if email:
                try:
                    pending_user = PendingUser.objects.get(email=email)
                except PendingUser.DoesNotExist:
                    return Response(
                        {"error": "Pending user not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                contact_info = email
            elif phone_number:
                try:
                    pending_user = PendingUser.objects.get(phone_number=phone_number)
                except PendingUser.DoesNotExist:
                    return Response(
                        {"error": "Pending user not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                contact_info = phone_number
            else:
                return Response(
                    {"error": "Email or phone number not found in session"},
                    status=status.HTTP_404_NOT_FOUND
                    )

            if pending_user.expiry_time > timezone.now():
                time_until_resend = pending_user.expiry_time - timezone.now()
                time_until_resend_sec = time_until_resend.total_seconds()
                return Response(
                    {"error": f"OTP already sent. Please wait {int(time_until_resend_sec)} seconds to resend."},
                    status=status.HTTP_400_BAD_REQUEST)
            else:
                otp = generate_otp()
                pending_user.otp = otp
                pending_user.expiry_time = timezone.now() + timedelta(
                    minutes=settings.OTP_EXPIRY_MINUTES
                )
                pending_user.save()
                try:
                    if '@' in contact_info:
                        contact_name=email.split('@')[0] 
                        send_otp_email(contact_info, contact_name, otp)
                    else:
                        send_otp(contact_info, otp)
                    return Response(
                        {"detail": "OTP resent successfully"},
                        status=status.HTTP_200_OK
                    )
                except Exception as e:
                    return Response(
                        {"error": "Failed to send OTP. Please try again later."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)