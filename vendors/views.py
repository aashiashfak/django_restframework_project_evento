from rest_framework import generics, status
from rest_framework.response import Response
from .models import Vendor
from .serializers import VendorSerializer, VerifyOTPSerializer
from .utilities import send_otp_email
from rest_framework.views import APIView
import random


class VendorSignUpView(APIView):
    def post(self, request):
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            try:
                request.session['vendor_signup_data'] = serializer.validated_data

                otp = ''.join(random.choices('0123456789', k=6))
                request.session['vendor_signup_otp'] = otp

                send_otp_email(serializer.validated_data['email'], serializer.validated_data['contact_name'], otp)

                return Response({"detail": "An OTP has been sent to your email address. Please use it to complete the sign-up process."}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": "Failed to send OTP email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class VerifyOTPView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            entered_otp = serializer.validated_data['otp']
            session_otp = request.session['vendor_signup_otp']

            if not session_otp:
                return Response({"error": "OTP not found in session"}, status=status.HTTP_400_BAD_REQUEST)

            if entered_otp == session_otp:
                vendor_serializer = VendorSerializer(data=request.session.get('vendor_signup_data'))
                if vendor_serializer.is_valid():
                    vendor = vendor_serializer.save(is_active=True, is_vendor=True)
                    return Response({"detail": "Vendor user created successfully"}, status=status.HTTP_200_OK)
                else:
                    return Response(vendor_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    