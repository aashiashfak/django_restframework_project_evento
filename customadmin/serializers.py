from accounts.models import CustomUser
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone
from accounts.serializers import CustomUserEmailSerializer
from accounts import constants
from . models import Category,Location
from accounts.models import CustomUser, Vendor

class SuperuserLoginSerializer(serializers.Serializer):
    """
    Serializer for authenticating superusers and generating JWT tokens.
    Returns A dictionary containing JWT tokens and user information
    if authentication is successful.
    If authentication fails, a ValidationError is raised with an appropriate
    error message.
    """
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        """
        Validate the provided username and password, and authenticate the superuser.
        """
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)
        if not user or not user.is_superuser:
            raise serializers.ValidationError(constants.INVALID_CREDENTIALS_ERROR)
        
        else:
            access_token = RefreshToken.for_user(user)
            refresh_token = RefreshToken.for_user(user)
            refresh_token_exp = timezone.now() + timedelta(days=10)
            user_serializer = CustomUserEmailSerializer(user)
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            return {
                "access_token": str(access_token.access_token),
                "refresh_token": str(refresh_token),
                "refresh_token_expiry": refresh_token_exp.isoformat(),  
                "user": user_serializer.data,  
                "message": constants.USER_LOGGED_IN_SUCCESSFULLY,
            }
    

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'image']

class LocationSerializer(serializers.ModelSerializer):
    """
    Serializer for Location model.
    """
    class Meta:
        model = Location
        fields = ['id', 'name']




class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone_number', 'is_active']


class VendorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Vendor
        fields = ['id', 'user', 'organizer_name']