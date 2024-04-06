from accounts.models import CustomUser
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone
from accounts.serializers import CustomUserEmailSerializer

class SuperuserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError('Username and password are required')
        
        user = authenticate(username=username, password=password)
        if user and not user.is_superuser:
            raise serializers.ValidationError('invalid credentials')
        else:
            access_token = RefreshToken.for_user(user)
            refresh_token = RefreshToken.for_user(user)
            refresh_token_exp = timezone.now() + timedelta(days=10)
            user_serializer = CustomUserEmailSerializer(user)

            return {
                "access_token": str(access_token.access_token),
                "refresh_token": str(refresh_token),
                "refresh_token_expiry": refresh_token_exp.isoformat(),  
                "user": user_serializer.data,  
                "message": "User logged in successfully",
            }