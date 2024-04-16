from rest_framework import serializers
from .models import Vendor
from django.core.validators import EmailValidator
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from accounts import constants
from accounts.utilities import validate_and_format_phone_number


email_validator = EmailValidator()





class VendorSignupSerializer(serializers.Serializer):
    """
    Serializer for vendor signup.
    This serializer validates and processes data for vendor registration.
    """

    
    organizer_name = serializers.CharField(max_length=255)
    pan_card_number = serializers.CharField(max_length=20)
    address = serializers.CharField()
    contact_name = serializers.CharField(max_length=255)
    email = serializers.EmailField(validators=[email_validator])
    password = serializers.CharField(max_length=255)
    confirm_password = serializers.CharField(max_length=255)
    phone_number = serializers.CharField()
    benificiary_name = serializers.CharField(max_length=255)
    account_type = serializers.CharField(max_length=100)
    bank_name = serializers.CharField(max_length=255)
    account_number = serializers.CharField(max_length=50)
    IFSC_code = serializers.CharField(max_length=20)


    def validate(self, data):
        """
        Validate the serializer data.
        This method checks for password match and uniqueness of email, phone number, etc.
        Returns Validated data if validation succeeds.
        Raises serializers.ValidationError If password does not match or email,
        phone number, etc. already exists.
        """
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError(constants.PASSWORDS_DO_NOT_MATCH_ERROR)
        
        phone_number = data.get('phone_number')
        formatted_phone_number = validate_and_format_phone_number(phone_number)
        data['phone_number'] = formatted_phone_number

        email = data.get('email')
        phone_number = data.get('phone_number')
        organizer_name = data.get('organizer_name')
        pan_card_number = data.get('pan_card_number')
        account_number = data.get('account_number')

        if email and Vendor.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists.")
        if phone_number and Vendor.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("Phone number already exists.")
        if organizer_name and Vendor.objects.filter(organizer_name=organizer_name).exists():
            raise serializers.ValidationError("organizer_name  already exists.")
        if pan_card_number and Vendor.objects.filter(pan_card_number=pan_card_number).exists():
            raise serializers.ValidationError("pan_card_number already exists.")
        if account_number and Vendor.objects.filter(account_number=account_number).exists():
            raise serializers.ValidationError("account number already exists.")

        return data


class VendorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Vendor model.

    """
    class Meta:
        model = Vendor
        fields = '__all__'


class VendorLoginSerializer(serializers.Serializer):
    """
    Serializer for vendor login.
    This serializer validates vendor credentials for login.
    Validates the provided credentials and generates 
    JWT tokens if validation succeeds.
    """

    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            vendor = Vendor.objects.get(email=email)
        except Vendor.DoesNotExist:
            raise serializers.ValidationError(
                {'error': 'Vendor with this email does not exist'}
            )

        if not check_password(password, vendor.password):
            raise serializers.ValidationError({'error': 'Invalid email or password'})

        if not vendor.is_vendor:
            raise serializers.ValidationError({'error': constants.INVALID_CREDENTIALS_ERROR})

        access_token = RefreshToken.for_user(vendor)
        refresh_token = RefreshToken.for_user(vendor)
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

class ChangePasswordSerializer(serializers.Serializer):
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
    GSTIN = serializers.BooleanField(required=False)
    ITR = serializers.BooleanField(required=False)
    contact_name = serializers.CharField(required=False)
    benificiary_name = serializers.CharField(required=False)
    account_type = serializers.CharField(required=False)
    bank_name = serializers.CharField(required=False)
    account_number = serializers.CharField(required=False)
    IFSC_code = serializers.CharField(required=False)

    class Meta:
        model = Vendor
        fields = (
            'organizer_name', 'pan_card_number', 'email', 'phone_number', 'address', 'GSTIN', 
            'ITR', 'contact_name', 'benificiary_name','account_type', 'bank_name',
            'account_number', 'IFSC_code',
        )

    def validate_organizer_name(self, value):
        user = self.context['request'].user
        if Vendor.objects.exclude(pk=user.pk).filter(organizer_name=value).exists():
            raise serializers.ValidationError({"organizer_name": "This organizer name is already in use."})
        return value

    def validate_pan_card_number(self, value):
        user = self.context['request'].user
        if Vendor.objects.exclude(pk=user.pk).filter(pan_card_number=value).exists():
            raise serializers.ValidationError({"pan_card_number": "This PAN card number is already in use."})
        return value

    def validate_account_number(self, value):
        user = self.context['request'].user
        if Vendor.objects.exclude(pk=user.pk).filter(account_number=value).exists():
            raise serializers.ValidationError({"account_number": "This account number is already in use."})
        return value

    def update(self, instance, validated_data):
        instance.organizer_name = validated_data.get('organizer_name', instance.organizer_name)
        instance.pan_card_number = validated_data.get('pan_card_number', instance.pan_card_number)
        instance.address = validated_data.get('address', instance.address)
        instance.GSTIN = validated_data.get('GSTIN', instance.GSTIN)
        instance.ITR = validated_data.get('ITR', instance.ITR)
        instance.contact_name = validated_data.get('contact_name', instance.contact_name)
        instance.benificiary_name = validated_data.get('benificiary_name', instance.benificiary_name)
        instance.account_type = validated_data.get('account_type', instance.account_type)
        instance.bank_name = validated_data.get('bank_name', instance.bank_name)
        instance.account_number = validated_data.get('account_number', instance.account_number)
        instance.IFSC_code = validated_data.get('IFSC_code', instance.IFSC_code)
        
        instance.save()
        return instance
