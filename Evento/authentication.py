from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from vendors.models import Vendor


def generate_token_for_user(user):
    refresh = RefreshToken.for_user(user)
    user_type = 'vendor' if isinstance(user, Vendor) else 'custom_user'
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user_id': user.id,
        'user_type': user_type
    }

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        User = get_user_model()
        user_id = validated_token['user_id']
        user_type = validated_token['user_type']

        if user_type == 'vendor':
            try:
                return Vendor.objects.get(pk=user_id)
            except Vendor.DoesNotExist:
                raise AuthenticationFailed('Vendor not found')
        
        elif user_type == 'custom_user':
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise AuthenticationFailed('CustomUser not found')
        
        raise AuthenticationFailed('Invalid user type')