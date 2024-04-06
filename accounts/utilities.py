from google.auth.transport import requests
from google.oauth2 import id_token
from .models import CustomUser
from django.contrib.auth import authenticate
from django.conf import settings
from .models import CustomUser, PendingUser
import random
from django.core.exceptions import ValidationError
from django.utils import timezone
import requests


class Google_signin():
    @staticmethod
    def validate(acess_token):
        try:
            id_info=id_token.verify_oauth2_token(acess_token,requests.Request())
            if 'accounts.google.com' in id_info['iss']:
                return id_info
        except Exception as e:
            return None
        
def login_google_user(email, password):
    user=authenticate(email=email,password=password)
    user_tokens=user.tokens()
    return {
       'email':user.email,
       'username':user.username,
       'access_token':str(user_tokens.get('access')),
       'refresh_token':str(user_tokens.get('refresh'))
    }
        
def register_google_user( email,username):
    user=CustomUser.objects.filter(email=email)
    if user.exists():
        login_google_user(email, settings.CUSTOM_PASSWORD_FOR_AUTH)
    else:   
        new_user={
            'email':email,
            'username':username,
            'password':settings.CUSTOM_PASSWORD_FOR_AUTH
        }
        register_user=CustomUser.objects.create_user(**new_user)
        register_user.is_active=True
        register_user.save()
        login_google_user(email, settings.CUSTOM_PASSWORD_FOR_AUTH)
        



#phone number login utilities
def generate_otp():
    return ''.join(random.choices('0123456789', k=6))

def send_otp(phone_number, otp):    
    message = f'Hello {otp}, This is a test message from spring edge '
    mobileno= f'91{phone_number}'
    sender = 'SEDEMO'
    apikey = '621492a44a89m36c2209zs4l7e74672cj'

    baseurl = 'https://instantalerts.co/api/web/send/?apikey='+apikey
    url= baseurl+'&sender='+sender+'&to='+mobileno+'&message='+message+'&format=json'
    response = requests.get(url)

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings

def create_Mobile_user(phone_number, otp):
    try:
        pending_user = PendingUser.objects.get(phone_number=phone_number, otp=otp)
        if pending_user.expiry_time >= timezone.now():
            # Check if the user already exists
            user = CustomUser.objects.filter(phone_number=phone_number).first()
            if user:
                return user
            else:
                # If user doesn't exist, create a new one
                new_user = CustomUser.objects.create_phone_user(phone_number=phone_number, password=settings.CUSTOM_PASSWORD_FOR_AUTH)
                new_user.is_active = True
                new_user.save()
                return new_user
        else:
            raise ValidationError("OTP has expired")
    except PendingUser.DoesNotExist:
        raise ValidationError("Invalid OTP")




def create_email_user(email, otp):
    try:
        pending_user = PendingUser.objects.get(email=email, otp=otp)
        if pending_user.expiry_time >= timezone.now():
            # Check if the user already exists
            user = CustomUser.objects.filter(email=email).first()
            if user:
                return user
            else:
                # If user doesn't exist, create a new one
                username = email.split('@')[0] 
                new_user = CustomUser.objects.create_user(email=email, username=username, password=settings.CUSTOM_PASSWORD_FOR_AUTH)
                new_user.is_active = True
                new_user.save()
                return new_user
        else:
            raise ValidationError("OTP has expired")
    except PendingUser.DoesNotExist:
        raise ValidationError("Invalid OTP")
