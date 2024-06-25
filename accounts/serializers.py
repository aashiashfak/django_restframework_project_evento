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
from .import constants


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
        print('userdata...........',user_data)
        try:
            user_data['sub']  
        except:
            raise serializers.ValidationError(
                constants.ERROR_TOKEN_EXPIRED_OR_INVALID
            )
        
        if user_data['aud'] != settings.GOOGLE_CLIENT_ID:
                raise AuthenticationFailed(constants.ERROR_VERIFY_USER)

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

    print('haai')

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
    email = serializers.CharField(max_length=200, required=False)
    phone_number = serializers.CharField(max_length=20, required=False)

        
class CustomUserEmailSerializer(serializers.ModelSerializer):
    """
    Serializer for the custom user model with email.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the user profile information.
    """

    username = serializers.CharField(required=False)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'profile_picture', 'tickets')
        read_only_fields = ('tickets',)

    def validate_username(self, value):
        """
        Validate the username to ensure it's unique among other users.
        """
        user = self.context['request'].user
        if CustomUser.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError({"username": constants.ERROR_USERNAME_IN_USE})
        return value

    def update(self, instance, validated_data):
        """
        Update the user's profile information.
        """
        instance.username = validated_data.get('username', instance.username)
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data['profile_picture']
        instance.save()
        return instance
    
    
    
class UpdateEmailSerializer(serializers.Serializer):
    """
    Serializer for updating user email address.
    """
    email = serializers.EmailField(validators=[EmailValidator()])

    def validate_email(self, value):
        """
        Validate the new email address.
        """
        user = self.context['request'].user
    
        if user.email == value:
            raise serializers.ValidationError(constants.ERROR_CURRENT_EMAIL)
        
        if CustomUser.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError(constants.ERROR_EMAIL_IN_USE)
        
        return value


class VerifyUpdateEmailOTPSerializer(serializers.Serializer):
    """
    Serializer for verifying and updating user email address with OTP.
    """
    otp = serializers.CharField(max_length=6)

    def validate_otp(self, value):
        """
        Validate OTP and email from session.
        """
        request = self.context['request']

        # Retrieve email from session
        email = request.session.get('email')
        
        if not email:
            raise serializers.ValidationError(constants.EMAIL_NOT_FOUND_ERROR)
        
        try:
            pending_user = PendingUser.objects.get(email=email)

            if pending_user.otp != value:
                raise serializers.ValidationError(constants.INVALID_OTP)
            
            if pending_user.expiry_time < timezone.now():
                raise serializers.ValidationError(constants.OTP_EXPIRED_ERROR)
                
        except PendingUser.DoesNotExist:
            raise serializers.ValidationError(constants.PENDING_USER_NOT_FOUND_ERROR)

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
    """
    Serializer for updating user phone number.
    """
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        """
        Validate and format phone number.
        """
        formatted_phone_number = validate_and_format_phone_number(value)
        
        user = self.context['request'].user
        
        if user.phone_number == formatted_phone_number:
            raise serializers.ValidationError(constants.ERROR_CURRENT_PHONE_NUMBER)

        if CustomUser.objects.exclude(pk=user.pk).filter(phone_number=formatted_phone_number).exists():
            raise serializers.ValidationError(constants.ERROR_PHONE_NUMBER_IN_USE)
        
        return formatted_phone_number


class VerifyUpdatePhoneOTPSerializer(serializers.Serializer):
    """
    Serializer for verifying and updating user phone number with OTP.
    """
    otp = serializers.CharField(max_length=6)

    def validate_otp(self, value):
        """
        Validate OTP and phone number from session.
        """
        request = self.context['request']

        # Retrieve phone number from session
        phone_number = request.session.get('phone_number')
        
        if not phone_number:
            raise serializers.ValidationError(constants.PHONE_NUMBER_NOT_FOUND)
        
        try:
            pending_user = PendingUser.objects.get(phone_number=phone_number)

            # Check if OTP has expired
            if pending_user.expiry_time < timezone.now():
                raise serializers.ValidationError(constants.OTP_EXPIRED_ERROR)

            if pending_user.otp != value:
                raise serializers.ValidationError(constants.INVALID_OTP)
                
        except PendingUser.DoesNotExist:
            raise serializers.ValidationError(constants.PENDING_USER_NOT_FOUND_ERROR)

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
            raise serializers.ValidationError(constants.OTP_EXPIRED_ERROR)

        instance.phone_number = phone_number
        instance.save(update_fields=['phone_number'])
        pending_user.delete()
        return instance

    



    

