from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from .serializers import (
    GoogleSignInSerializer,
    PhoneOTPRequestSerializer,
    OTPVerificationSerializer,
    EmailOTPRequestSerializer,
    CustomUserEmailSerializer,
    UserProfileSerializer,
    UpdateEmailSerializer,
    VerifyUpdateOTPSerializer,
    UpdatePhoneSerializer,
    FollowSerializer,
    CustomUserPhoneSerializer,
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, permissions 
from .models import PendingUser
from datetime import timedelta
from django.conf import settings
from vendors.utilities import send_otp_email
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .utilities import (
    send_otp,
    create_Mobile_user,
    generate_otp,
    create_email_user
)
from .import constants
from .models import Vendor, Follow, CustomUser



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
                print("stored email in session:",email)
                username = email.split('@')[0] 
                otp = generate_otp()
                print(f"your otp is {otp}")
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
                        {"detail": constants.OTP_SENT_SUCCESSFULLY},
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
                    {"error": constants.EMAIL_NOT_PROVIDED_ERROR},
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
            print(otp)
            # email = request.session.get('email')
            email = serializer.validated_data.get('email')
            print("Retrieved email from serializer:",email)
            if not email:
                return Response(
                    {"error": constants.EMAIL_NOT_FOUND_ERROR},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if otp:
                try:
                    pending_user = PendingUser.objects.get(email=email, otp=otp)
                    if pending_user.expiry_time >= timezone.now():
                        print(timezone.now())
                        print(otp)

                        user = create_email_user(email)
                        pending_user.delete()

                        access_token = RefreshToken.for_user(user)
                        refresh_token = RefreshToken.for_user(user)
                        
                        refresh_token_exp = timezone.now() + timedelta(days=100)

                        user_serializer = CustomUserEmailSerializer(user)

                        return Response({
                            "access_token": str(access_token.access_token),
                            "refresh_token": str(refresh_token),
                            "refresh_token_expiry": refresh_token_exp.isoformat(),  
                            "user": user_serializer.data,  
                            "message": constants.USER_LOGGED_IN_SUCCESSFULLY,
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response(
                            {"error": constants.OTP_EXPIRED_ERROR},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except PendingUser.DoesNotExist:
                    return Response(
                        {"error": constants.INVALID_OTP},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"error": constants.INVALID_OTP},
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
            print(f'your phone number is {phone_number}')
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
                        {"detail": constants.OTP_SENT_SUCCESSFULLY},
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
                    {"error": constants.PHONE_NUMBER_NOT_PROVIDED},
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
            phone_number = serializer.validated_data.get('phone_number')
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

                        user_serializer = CustomUserPhoneSerializer(user)

                        return Response({
                            "access_token": str(access_token.access_token),
                            "refresh_token": str(refresh_token),
                            "refresh_token_expiry": refresh_token_expiry.isoformat(), 
                            "user": user_serializer.data,  
                            "detail": constants.USER_LOGGED_IN_SUCCESSFULLY,
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response(
                            {"error": constants.OTP_EXPIRED_ERROR},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except PendingUser.DoesNotExist:
                    return Response(
                        {"error": constants.INVALID_OTP},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"error": constants.PHONE_NUMBER_NOT_FOUND},
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
            email = request.data.get('email')
            phone_number = request.data.get('phone_number')
            print('email', email)
            print('PhoneNumber', phone_number)

            if email:
                try:
                    pending_user = PendingUser.objects.get(email=email)
                except PendingUser.DoesNotExist:
                    return Response(
                        {"error": constants.PENDING_USER_NOT_FOUND_ERROR},
                        status=status.HTTP_404_NOT_FOUND
                    )
                contact_info = email
            elif phone_number:
                try:
                    pending_user = PendingUser.objects.get(phone_number=phone_number)
                except PendingUser.DoesNotExist:
                    return Response(
                        {"error": constants.PENDING_USER_NOT_FOUND_ERROR},
                        status=status.HTTP_404_NOT_FOUND
                    )
                contact_info = phone_number
            else:
                return Response(
                    {"error": constants.CONTACT_INFO_NOT_FOUND_ERROR},
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
                        {"detail": constants.OTP_RESENT_SUCCESSFULLY},
                        status=status.HTTP_200_OK
                    )
                except Exception as e:
                    return Response(
                        {"error": constants.FAILED_TO_SEND_OTP_ERROR},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserProfileAPIView(APIView):
    """
    View for retrieving and updating user profile information.
    """
    permission_classes = [IsAuthenticated]
    serializer_class=UserProfileSerializer
    def get(self, request):
        """
        Retrieve the profile information of the authenticated user.
        """
        try:
            serializer = self.serializer_class(request.user, context={'request': request})
            return Response(serializer.data)
        except PermissionDenied:
            return Response({'error': constants.AUTHENTICATION_FAILED}, status=status.HTTP_401_UNAUTHORIZED)

    def put(self, request):
        """
        Update the profile information of the authenticated user.
        """
        try:
            serializer = UserProfileSerializer(request.user, data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied:
            return Response({'error': constants.AUTHENTICATION_FAILED}, status=status.HTTP_401_UNAUTHORIZED)


class UpdateEmailAPIView(APIView):
    """
    API view for updating email and sending OTP.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Update email and send OTP.
        """
        serializer = UpdateEmailSerializer(data=request.data, context={'request': request})

        print('entered in updated otp view ')
        
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            print(email)
            request.session['email'] = email
            
            # Create or update PendingUser
            pending_user, created = PendingUser.objects.update_or_create(
                defaults={
                    'email': email,
                    'otp': generate_otp(),
                    'expiry_time': timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
                }
            )
            try:
                send_otp_email(email, request.user.username, pending_user.otp)
                
                return Response({"detail":constants.OTP_SENT_SUCCESSFULLY}, status=status.HTTP_200_OK)
            
            except Exception as e:
                pending_user.delete()
                return Response({"error": constants.FAILED_TO_SEND_OTP_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyUpdateEmailOTPView(APIView):
    """
    View to verify OTP and update user's email.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyUpdateOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)

            return Response({"message": constants.EMAIL_UPDATED_SUCCESSFULLY})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdatePhoneAPIView(APIView):
    """
    API view for updating phone number and sending OTP.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Update phone number and send OTP.
        """
        serializer = UpdatePhoneSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            phone_number = serializer.validated_data.get('phone_number')
            request.session['phone_number'] = phone_number
            
            # Create or update PendingUser
            pending_user, created = PendingUser.objects.update_or_create(
                defaults={
                    'phone_number': phone_number,
                    'otp': generate_otp(),
                    'expiry_time': timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
                }
            )
            try:
                send_otp(phone_number, pending_user.otp)
                
                return Response({"detail": constants.OTP_SENT_SUCCESSFULLY}, status=status.HTTP_200_OK)
            
            except Exception as e:
                pending_user.delete()
                return Response({"error": constants.FAILED_TO_SEND_OTP_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyUpdatePhoneOTPView(APIView):
    """
    View to verify OTP and update user's phone number.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyUpdateOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)

            return Response({"message": constants.PHONE_UPDATED_SUCCESSFULLY})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FollowUnfollowVendorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, vendor_id):
        follower = request.user
        print('user.....',follower)
        try:
            vendor = Vendor.objects.get(id=vendor_id)
            print('vendor.....',vendor)
        except Vendor.DoesNotExist:
            return Response({"detail": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if Follow.objects.filter(follower=follower, vendor=vendor).exists():
            return Response({"detail": "You are already following this vendor."}, status=status.HTTP_400_BAD_REQUEST)

        follow = Follow.objects.create(follower=follower, vendor=vendor)
        serializer = FollowSerializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, vendor_id):
        follower = request.user
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"detail": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)
        
        follow = Follow.objects.filter(follower=follower, vendor=vendor)
        if not follow.exists():
            return Response({"detail": "You are not following this vendor."}, status=status.HTTP_400_BAD_REQUEST)

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
class VendorFollowStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, vendor_id):
        try:
            vendor = Vendor.objects.get(id=vendor_id)
            is_followed = Follow.objects.filter(follower=request.user, vendor=vendor).exists()
            return Response({"is_followed": is_followed}, status=status.HTTP_200_OK)
        except Vendor.DoesNotExist:
            return Response({"detail": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)