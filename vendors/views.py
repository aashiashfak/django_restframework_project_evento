# from rest_framework import status
# from rest_framework.response import Response

from .serializers import (
    VendorSignupSerializer,
    VendorSerializer,
    VendorLoginSerializer,
    EmailSerializer,
    ChangeForgetPasswordSerializer,
    VendorProfileSerializer,
)
# from rest_framework.views import APIView
# from django.utils import timezone
# from datetime import timedelta
from accounts.serializers import OTPVerificationSerializer
# from accounts.models import PendingUser
from django.conf import settings
from accounts.utilities import generate_otp
from .utilities import send_otp_email
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from accounts import constants
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from accounts.models import CustomUser,PendingUser,VendorManager
from accounts.permissions import IsVendor




from rest_framework import status,generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import VendorSignupSerializer
from django.utils import timezone
from datetime import timedelta


class VendorSignupView(APIView):
    """
    View for vendor signup.
    This view handles the signup process for vendors. It sends an OTP to the 
    provided email address for verification before creating the vendor account.
    """
    def post(self, request):
        """
        Handle POST request for vendor signup.
        This method validates the provided data, sends an OTP to the provided 
        email address, and stores the vendor signup data in the session.
        Return Response object containing the result of the signup operation.
        """
        serializer = VendorSignupSerializer(data=request.data)
        if serializer.is_valid():
            # Save data in session
            request.session['vendor_signup_data'] = serializer.validated_data

            # Get email from validated data
            email = serializer.validated_data['email']

            otp = generate_otp()
            expiry_time = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
            pending_user, created = PendingUser.objects.update_or_create(
                email=email,
                defaults={'otp': otp, 'expiry_time': expiry_time}
            )

            try:
                send_otp_email(email, serializer.validated_data['contact_name'], otp)
                return Response({'message': 'OTP sent successfully.'}, status=status.HTTP_200_OK)
            except Exception as e:
                pending_user.delete()
                return Response({'error': 'Failed to send OTP.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class VendorVerifyOtpView(APIView):
    """
    View for verifying OTP during vendor signup.
    This view handles the verification of OTP sent during the vendor signup process.
    """
    def post(self, request):
        """
        Handle POST request for OTP verification.
        This method validates the OTP provided by the user and creates the vendor 
        account if the OTP is valid.
        Returns Response object containing the result of the OTP verification process.
        """
        try:
            email = request.session['vendor_signup_data']['email']
        except KeyError:
            return Response(
                {'error': constants.EMAIL_NOT_FOUND_ERROR},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        otp_serializer = OTPVerificationSerializer(data=request.data)
        if otp_serializer.is_valid():
            otp = otp_serializer.validated_data['otp']
            if email:
                try:
                    pending_user = PendingUser.objects.get(email=email, otp=otp)
                    if pending_user.expiry_time < timezone.now():
                        pending_user.delete()
                        return Response(
                            {'error': constants.OTP_EXPIRED_ERROR},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    vendor_data = request.session.get('vendor_signup_data')
                    vendor_data.pop('confirm_password')
                    password = vendor_data.pop('password')
                    
                    # Create vendor user and vendor using custom manager
                    vendor_manager = VendorManager()
                    user, vendor = vendor_manager.create_vendor_user(vendor_data, password)
                    
                    access_token = RefreshToken.for_user(user)
                    refresh_token = RefreshToken.for_user(user)
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
                    return Response(
                        {'error': constants.INVALID_OTP},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        else:
            return Response(otp_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorLoginView(APIView):
    """
    View for vendor login.
    This view handles the authentication of vendor login requests.
    """

    def post(self, request):
        """
        Handle POST request for vendor login.
        This method validates the provided credentials and generates access tokens
        for authenticated vendors.
        """
        serializer = VendorLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VendorForgetPasswordOTPsent(APIView):
    """
    View for sending OTP during forget password process.
    """
    def post(self, request):
        """
        Handle POST request for sending OTP.
        This method sends an OTP to the email address of the vendor who wants to
        reset their password.
        """
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            contact_name = email.split('@')[0]  
            otp = generate_otp()

            try:
                vendor = CustomUser.objects.get(email=email)
                if not vendor.is_vendor:
                    return Response(
                        {"error": "Vendor with this email does not exist"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
                expiry_time = timezone.now() + timedelta(
                    minutes=settings.OTP_EXPIRY_MINUTES
                )
                pending_user, created = PendingUser.objects.update_or_create(
                    email=email,
                    defaults={'otp': otp, 'expiry_time': expiry_time}
                )

                try:
                    send_otp_email(email, contact_name, otp)
                    return Response(
                        {"detail": constants.OTP_SENT_SUCCESSFULLY},
                        status=status.HTTP_200_OK
                    )
                except Exception:
                    pending_user.delete()
                    return Response(
                        {"error": constants.FAILED_TO_SEND_OTP_ERROR},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except CustomUser.DoesNotExist:
                return Response(
                    {"error": "Vendor with this email does not exist"},
                    status=status.HTTP_404_NOT_FOUND
                    )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyOTPView(APIView):
    """
    View for verifying OTP.
    This view handles the verification of OTP sent during various processes,
    such as password reset.
    """
    def post(self, request):
        """
        Handle POST request for OTP verification.
        This method validates the OTP provided by the user 
        Return Response object containing the result of the OTP verification process.
        """
        serializer = OTPVerificationSerializer(data=request.data) 
        if serializer.is_valid():
            otp = request.data.get('otp')
            try:
                email = request.session['email']
            except Exception:
                return Response(
                    {"error": constants.EMAIL_NOT_FOUND_ERROR},
                    status=status.HTTP_404_NOT_FOUND
                )
            try:
                pending_user = PendingUser.objects.get(email=email, otp=otp)
                if pending_user.expiry_time < timezone.now():
                    pending_user.delete()
                    return Response(
                        {'error': constants.OTP_EXPIRED_ERROR},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    pending_user.delete()
                    return Response(
                        {'detail': 'OTP verified successfully'},
                        status=status.HTTP_200_OK
                    )
            except PendingUser.DoesNotExist:
                return Response(
                    {'error': constants.INVALID_OTP},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class ChangePasswordView(APIView):
    """
    View for changing vendor password.
    """
    def post(self, request):
        """
        Handle POST request for changing password.
        This method validates the provided data and changes the password of the vendor.
        Return Response object containing the result of the password change process.
        """
        serializer = ChangeForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            new_password = serializer.validated_data.get('password')
            hashed_password = make_password(new_password)
            email = request.session.get('email')
            if email:
                try:
                    vendor = CustomUser.objects.get(email=email)
                    vendor.password = hashed_password
                    vendor.save(update_fields=['password'])
                    return Response(
                        {"detail": "Password changed successfully"},
                        status=status.HTTP_200_OK
                        )
                except CustomUser.DoesNotExist:
                    return Response(
                        {"error": "Vendor with this email does not exist"},
                        status=status.HTTP_404_NOT_FOUND
                        )
            else:
                return Response(
                    {"error": constants.EMAIL_NOT_FOUND_ERROR},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


from django.shortcuts import get_object_or_404        
from events.models import Event,TicketType
from events.serializers import (
    EventCreateSerializer,
    EventRetrieveSerializer,
    EventUpdateSerializer,
    TicketTypeSerializer

)

 

class VendorProfileAPIView(APIView):
    """
    View for retrieving and updating vendor profile information.
    """
    permission_classes = [IsAuthenticated, IsVendor]
    
    def get(self, request):
        """
        Retrieve the profile information of the authenticated vendor.
        """
        vendor = getattr(request.user, 'vendor', None)
        
        if not vendor:
            return Response({'error': 'Vendor profile does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the Vendor data using VendorSerializer
        serializer = VendorSerializer(vendor)
        return Response(serializer.data)

    def put(self, request):
        """
        Update the profile information of the authenticated vendor.
        """
        vendor = getattr(request.user, 'vendor', None)
        
        if not vendor:
            return Response({'error': 'Vendor profile does not exist'}, status=status.HTTP_404_NOT_FOUND)

        serializer = VendorProfileSerializer(vendor, data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        



class CreateEventView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get(self, request):
        events = Event.objects.filter(vendor=request.user)
        serializer = EventCreateSerializer(events, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EventCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Assign vendor_id before saving the event
            serializer.validated_data['vendor_id'] = request.user.id  # Assuming user is authenticated vendor
            
            # Save the event
            event = serializer.save()
            
            # Return success response
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Return error response if serializer is invalid
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


        

class VendorEventDetailView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id, vendor=request.user)
        serializer = EventRetrieveSerializer(event)
        return Response(serializer.data)

    def put(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
            
        serializer = EventUpdateSerializer(instance=event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id, vendor=request.user)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


class TicketTypeListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TicketTypeSerializer
    permission_classes = [IsAuthenticated, IsVendor]

    def get_queryset(self):
        # Filter ticket types created by the authenticated user
        return TicketType.objects.filter(event__vendor=self.request.user)

class TicketTypeDetailUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    permission_classes = [IsAuthenticated, IsVendor]

    def get_serializer(self, *args, **kwargs):
        kwargs['partial'] = True
        return super().get_serializer(*args, **kwargs)