from django.utils import timezone
from rest_framework import serializers
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from .utilities import (
    Google_signin,
    register_google_user,
    validate_and_format_phone_number
)
from .models import CustomUser,PendingUser
from django.core.validators import EmailValidator
from rest_framework.exceptions import PermissionDenied
from events.serializers import TicketSerializer



class GoogleSignInSerializer(serializers.Serializer):
    """
    Serializer for Google sign-in.
    """
    access_token=serializers.CharField(min_length=6)

    def validate_access_token(self, access_token):
        """
        Validate the access token and register the user if valid.
        """
        user_data=Google_signin.validate(access_token)
        try:
            user_data['sub']  
        except:
            raise serializers.ValidationError(
                "this token has expired or invalid please try again"
            )
        
        if user_data['aud'] != settings.GOOGLE_CLIENT_ID:
                raise AuthenticationFailed('Could not verify user.')

        email=user_data['email']
        username = email.split('@')[0] 
        return register_google_user(email, username)

class EmailOTPRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting OTP via email. 
    This serializer saves pending user data for checking while verifying OTP.
    """
    email=serializers.CharField(max_length=255)
    class Meta:
        model = PendingUser
        fields = [
            'email',
            'otp',
            'expiry_time',
        ]

class PhoneOTPRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting OTP via phone number.
    This serializer saves pending user data for checking while verifying OTP.
    """
    phone_number = serializers.CharField()

    class Meta:
        model = PendingUser
        fields = [
            'phone_number',
            'otp',
            'expiry_time',
        ]
    def validate_phone_number(self, value):
        """
        Validate phone number using phonenumbers library.
        """
        return validate_and_format_phone_number(value)

    # def validate_phone_number(self, value):
    #     """
    #     Validate phone number to ensure it has exactly 10 digits.
    #     """
    #     if len(value) != 10 or not value.isdigit():
    #         raise serializers.ValidationError(
    #             "Phone number must be a 10-digit number."
    #         )
    #     return value
        
    
class OTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for OTP verification.
    """
    otp = serializers.CharField(max_length=6)


        
class CustomUserEmailSerializer(serializers.ModelSerializer):
    """
    Serializer for the custom user model with email.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email']


class UserProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(required=False)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'profile_picture', 'tickets')
        read_only_fields = ('tickets',)

    def validate_username(self, value):
        user = self.context['request'].user
        if CustomUser.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError({"username": "This username is already in use."})
        return value

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data['profile_picture']
        instance.save()
        return instance
    
    
    
class UpdateEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[EmailValidator()])

    def validate_email(self, value):
        user = self.context['request'].user
    
        if user.email == value:
            raise serializers.ValidationError("This is your current email.")
        
        if CustomUser.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        
        return value


class VerifyUpdateEmailOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)

    def validate_otp(self, value):
        """
        Validate OTP and email from session.
        """
        request = self.context['request']

        # Retrieve email from session
        email = request.session.get('email')
        
        if not email:
            raise serializers.ValidationError("Email not found in session")
        
        try:
            pending_user = PendingUser.objects.get(email=email)

            if pending_user.otp != value:
                raise serializers.ValidationError("Invalid OTP")
            
            if pending_user.expiry_time < timezone.now():
                raise serializers.ValidationError("OTP has expired")
                
        except PendingUser.DoesNotExist:
            raise serializers.ValidationError("Pending user not found")

        return value

    def update(self, instance, validated_data):
        """
        Update user's email.
        """
        request = self.context['request']
        email= request.session.get('email')
        pending_user = PendingUser.objects.get(email=email)
        instance.email = email
        instance.save()
        pending_user.delete()
        return instance


class UpdatePhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        """
        Validate and format phone number.
        """
        formatted_phone_number = validate_and_format_phone_number(value)
        
        user = self.context['request'].user
        
        if user.phone_number == formatted_phone_number:
            raise serializers.ValidationError("This is your current phone number.")

        if CustomUser.objects.exclude(pk=user.pk).filter(phone_number=formatted_phone_number).exists():
            raise serializers.ValidationError("Phone number is already in use.")
        
        return formatted_phone_number


class VerifyUpdatePhoneOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)

    def validate_otp(self, value):
        """
        Validate OTP and phone number from session.
        """
        request = self.context['request']

        # Retrieve phone number from session
        phone_number = request.session.get('phone_number')
        
        if not phone_number:
            raise serializers.ValidationError("Phone number not found in session")
        
        try:
            pending_user = PendingUser.objects.get(phone_number=phone_number)

            # Check if OTP has expired
            if pending_user.expiry_time < timezone.now():
                raise serializers.ValidationError("OTP has expired")

            if pending_user.otp != value:
                raise serializers.ValidationError("Invalid OTP")
                
        except PendingUser.DoesNotExist:
            raise serializers.ValidationError("Pending user not found")

        return value

    def update(self, instance, validated_data):
        """
        Update user's phone number.
        """
        request = self.context['request']
        phone_number = request.session.get('phone_number')
        
        pending_user = PendingUser.objects.get(phone_number=phone_number)
        
        # Check again if OTP has expired before updating phone number
        if pending_user.expiry_time < timezone.now():
            raise serializers.ValidationError("OTP has expired")

        instance.phone_number = phone_number
        instance.save()
        pending_user.delete()
        return instance

    



    

