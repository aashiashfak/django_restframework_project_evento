from rest_framework import serializers
from .models import Vendor
from django.core.validators import EmailValidator, RegexValidator

from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import check_password



email_validator = EmailValidator()
phone_regex = RegexValidator(
    regex=r'^\d{10}$',
    message='Phone number must be 10 digits only',
)

from rest_framework import serializers

class VendorSignupSerializer(serializers.Serializer):
    organizer_name = serializers.CharField(max_length=255)
    pan_card_number = serializers.CharField(max_length=20)
    address = serializers.CharField()
    contact_name = serializers.CharField(max_length=255)
    email = serializers.EmailField(validators=[email_validator])
    password = serializers.CharField(max_length=255)
    confirm_password = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=10, validators=[phone_regex])
    benificiary_name = serializers.CharField(max_length=255)
    account_type = serializers.CharField(max_length=100)
    bank_name = serializers.CharField(max_length=255)
    account_number = serializers.CharField(max_length=50)
    IFSC_code = serializers.CharField(max_length=20)


    def validate(self, data):
        """
        Validate the serializer data.
        """
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

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
            raise serializers.ValidationError("Phone number already exists.")




        return data


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'


class VendorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            vendor = Vendor.objects.get(email=email)
        except Vendor.DoesNotExist:
            raise serializers.ValidationError({'error': 'Vendor with this email does not exist'})

        if not check_password(password, vendor.password):
            raise serializers.ValidationError({'error': 'Invalid email or password'})

        if not vendor.is_vendor:
            raise serializers.ValidationError({'error': 'Invalid credentials'})

        access_token = RefreshToken.for_user(vendor)
        refresh_token = RefreshToken.for_user(vendor)
        refresh_token_exp = timezone.now() + timezone.timedelta(days=10)
        vendor_serializer = VendorSerializer(vendor)

        return {
            "access_token": str(access_token.access_token),
            "refresh_token": str(refresh_token),
            "refresh_token_expiry": refresh_token_exp.isoformat(),  
            "user": vendor_serializer.data,  
            "message": "User logged in successfully",
        }
