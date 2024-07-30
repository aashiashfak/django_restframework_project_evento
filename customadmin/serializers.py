from accounts.models import CustomUser
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone
from accounts.serializers import CustomUserEmailSerializer
from accounts import constants
from . models import Category,Location,Banner
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

    def validate_name(self, value):
        """
        Check if the category name is unique.
        """
        if Category.objects.filter(name=value).exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value

    def validate(self, data):
        """
        Ensure all required fields are present during creation or update.
        """
        errors = {}
        
        # Custom validation for existing instance (update scenario)
        if self.instance:
            if 'name' in data and Category.objects.filter(name=data['name']).exists():
                errors['name'] = "A category with this name already exists."
        
        # Custom validation for new instance (creation scenario)
        if not self.instance:
            if not data.get('name'):
                errors['name'] = "Name field is required."
            if 'image' not in data or data['image'] is None:
                errors['image'] = "Image field is required."
        
        if errors:
            # Raise ValidationError with custom errors
            raise serializers.ValidationError(errors)

        return data

class LocationSerializer(serializers.ModelSerializer):
    """
    Serializer for Location model.
    """
    class Meta:
        model = Location
        fields = ['id', 'name']

    def validate(self, data):
        """
        Ensure all required fields are present during creation or update.
        """
        errors = []
        
        if 'name' not in data or not data['name'].strip():
            errors.append("This field is required.")
        elif Location.objects.filter(name=data['name']).exists():
            errors.append("A location with this name already exists.")
        
        if errors:
            raise serializers.ValidationError({"error": " ".join(errors)})

        return data


class BannerSerializer(serializers.ModelSerializer):
    """
    Serializer for Banner model.
    """
    class Meta:
        model = Banner
        fields = ['id', 'image', 'description']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone_number', 'is_active', 'is_vendor' ]


class VendorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Vendor
        fields = ['id', 'organizer_name','user' ]