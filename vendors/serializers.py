from rest_framework import serializers
from .models import Vendor


from rest_framework import serializers
from .models import Vendor

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            'organizer_name',
            'pan_card_number',
            'address',
            'GSTIN',
            'ITR',
            'contact_name',
            'email',
            'password',
            # 'conform password',
            'phone_number',
            'benificiary_name',
            'account_type',
            'bank_name',
            'account_number',
            'IFSC_code',
        ]
def validate(self, data):
    """
    Validate the serializer data.
    """
    # Check if password and password_confirm match
    password = data.get('password')
    password_confirm = data.get('password_confirm')
    if password and password_confirm and password != password_confirm:
        raise serializers.ValidationError("Passwords do not match.")

    # Check if mobile_number is present and is 10 digits
    mobile_number = data.get('mobile_number')
    if mobile_number:
        if len(mobile_number) != 10 or not mobile_number.isdigit():
            raise serializers.ValidationError("Phone number must be a 10-digit number.")

    # Check if email and phone_number are unique
    email = data.get('email')
    phone_number = data.get('phone_number')
    if email and Vendor.objects.filter(email=email).exists():
        raise serializers.ValidationError("Email already exists.")
    if phone_number and Vendor.objects.filter(phone_number=phone_number).exists():
        raise serializers.ValidationError("Phone number already exists.")

    return data

class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)