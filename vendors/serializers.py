from rest_framework import serializers
from accounts.models import Vendor,CustomUser
from django.core.validators import EmailValidator
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from accounts import constants
from accounts.utilities import validate_and_format_phone_number
from rest_framework import serializers
from django.contrib.auth import get_user_model


email_validator = EmailValidator()




from rest_framework import serializers
from accounts.models import Vendor
from django.core.validators import EmailValidator

email_validator = EmailValidator()

class VendorSignupSerializer(serializers.Serializer):
    organizer_name = serializers.CharField(max_length=255)
    pan_card_number = serializers.CharField(max_length=20)
    address = serializers.CharField()
    contact_name = serializers.CharField(max_length=255)
    email = serializers.EmailField(validators=[email_validator])
    phone_number = serializers.CharField(max_length=15)
    benificiary_name = serializers.CharField(max_length=255)
    account_type = serializers.CharField(max_length=100)
    bank_name = serializers.CharField(max_length=255)
    account_number = serializers.CharField(max_length=50)
    IFSC_code = serializers.CharField(max_length=20)
    password = serializers.CharField(max_length=255)
    confirm_password = serializers.CharField(max_length=255)

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError(constants.PASSWORDS_DO_NOT_MATCH_ERROR)
        
        phone_number = data.get('phone_number')
        validate_and_format_phone_number(phone_number)

        email = data.get('email')
        pan_card_number = data.get('pan_card_number')
        account_number = data.get('account_number')
        organizer_name = data.get('organizer_name')

        if email and CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(constants.ERROR_EMAIL_IN_USE)
        if phone_number and CustomUser.objects.filter(phone_number=phone_number).exists() :
            raise serializers.ValidationError(constants.ERROR_PHONE_NUMBER_IN_USE)
        if organizer_name and  Vendor.objects.filter(organizer_name=organizer_name).exists():
            raise serializers.ValidationError(constants.ERROR_ORGANIZER_NAME_EXISTS)
        if pan_card_number and Vendor.objects.filter(pan_card_number=pan_card_number).exists():
            raise serializers.ValidationError(constants.ERROR_PAN_EXISTS)
        if account_number and Vendor.objects.filter(account_number=account_number).exists():
            raise serializers.ValidationError(constants.ERROR_ACCOUNT_NUMBER_EXISTS)
        

        return data
    
class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model.
    """
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'profile_picture')  

class VendorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Vendor model.
    """
    user = CustomUserSerializer(read_only=True)
    class Meta:

        model = Vendor
        fields = '__all__'

CustomUser = get_user_model()

class VendorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            custom_user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({'error': constants.ERROR_VENDOR_EMAIL_NOT_FOUND})

        if not check_password(password, custom_user.password):
            raise serializers.ValidationError({'error': constants.INVALID_CREDENTIALS_ERROR})

        if not custom_user.is_vendor:
            raise serializers.ValidationError(constants.INVALID_CREDENTIALS_ERROR)

        try:
            vendor = custom_user.vendor_details  # Access the Vendor object associated with the CustomUser
        except Vendor.DoesNotExist:
            raise serializers.ValidationError({'error': constants.ERROR_VENDOR_PROFILE_NOT_FOUND})

        access_token = RefreshToken.for_user(custom_user)
        refresh_token = RefreshToken.for_user(custom_user)
        refresh_token_exp = timezone.now() + timezone.timedelta(days=10)

        vendor_serializer = VendorSerializer(vendor)

        return {
            "access_token": str(access_token.access_token),
            "refresh_token": str(refresh_token),
            "refresh_token_expiry": refresh_token_exp.isoformat(),
            "user": vendor_serializer.data,
            "message": constants.USER_LOGGED_IN_SUCCESSFULLY,
        }

class EmailSerializer(serializers.Serializer):
    """
    Serializer for validating email.
    """
    email = serializers.EmailField(validators=[EmailValidator()])

class ChangeForgetPasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.

    This serializer validates and processes data for changing the user's password.
    """
    password = serializers.CharField(max_length=255)
    confirm_password = serializers.CharField(max_length=255)

    def validate(self, data):
        """
        Validates the serializer data and checks if passwords match.
        """
    
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError(constants.PASSWORDS_DO_NOT_MATCH_ERROR)

        return data
    

class VendorProfileSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(required=False)
    pan_card_number = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    contact_name = serializers.CharField(required=False)
    benificiary_name = serializers.CharField(required=False)
    account_type = serializers.CharField(required=False)
    bank_name = serializers.CharField(required=False)
    account_number = serializers.CharField(required=False)
    IFSC_code = serializers.CharField(required=False)
    profile_picture = serializers.ImageField(required=False, source='user.profile_picture')    

    class Meta:
        model = Vendor
        fields = (
            'organizer_name', 'pan_card_number', 'address', 'contact_name', 'benificiary_name',
            'account_type', 'bank_name', 'account_number', 'IFSC_code', 'profile_picture'
        )

    def validate_organizer_name(self, value):
        vendor = self.context['request'].user.vendor_details
        if Vendor.objects.exclude(pk=vendor.pk).filter(organizer_name=value).exists():
            raise serializers.ValidationError({constants.ERROR_ORGANIZER_NAME_EXISTS})
        return value

    def validate_pan_card_number(self, value):
        vendor = self.context['request'].user.vendor_details
        if Vendor.objects.exclude(pk=vendor.pk).filter(pan_card_number=value).exists():
            raise serializers.ValidationError({constants.ERROR_PAN_EXISTS})
        return value

    def validate_account_number(self, value):
        vendor = self.context['request'].user.vendor_details
        if Vendor.objects.exclude(pk=vendor.pk).filter(account_number=value).exists():
            raise serializers.ValidationError({constants.ERROR_ACCOUNT_NUMBER_EXISTS})
        return value

    def update(self, instance, validated_data):
        instance.organizer_name = validated_data.get('organizer_name', instance.organizer_name)
        instance.pan_card_number = validated_data.get('pan_card_number', instance.pan_card_number)
        instance.address = validated_data.get('address', instance.address)
        instance.contact_name = validated_data.get('contact_name', instance.contact_name)
        instance.benificiary_name = validated_data.get('benificiary_name', instance.benificiary_name)
        instance.account_type = validated_data.get('account_type', instance.account_type)
        instance.bank_name = validated_data.get('bank_name', instance.bank_name)
        instance.account_number = validated_data.get('account_number', instance.account_number)
        instance.IFSC_code = validated_data.get('IFSC_code', instance.IFSC_code)
        
        instance.save()

        profile_picture = validated_data.get('profile_picture')
        if profile_picture:
            user = instance.user
            user.profile_picture = profile_picture
            user.save(update_fields=['profile_picture'])

        
        return instance
