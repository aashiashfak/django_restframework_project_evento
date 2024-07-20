from google.auth.transport import requests
from google.oauth2 import id_token
from .models import CustomUser
from django.contrib.auth import authenticate
from django.conf import settings
from .models import CustomUser
import random
from django.utils import timezone
import requests as req
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from rest_framework import serializers
from .import constants
from rest_framework.exceptions import AuthenticationFailed





class Google_signin():
    """
    Class for Google Sign-In authentication.
    """
    @staticmethod
    def validate(acess_token):
        """
        Validate Google access token.

        The access token received from Google.

        Returns User data if validation is successful, otherwise None.
        """
        print('entered in validate fn')
        try:
            id_info=id_token.verify_oauth2_token(acess_token,requests.Request(),settings.GOOGLE_CLIENT_ID)
            print('id_info..........',id_info)
            if 'accounts.google.com' in id_info['iss']:
                return id_info
        except Exception as e:
            return None
        
def login_google_user(email):
    user = CustomUser.objects.filter(email=email).first()
    if not user:
        raise AuthenticationFailed("Invalid login credentials")
    user_tokens = user.tokens
    return user, user_tokens


def register_google_user(email, username):
    """
    Register a new user with Google credentials.

    Returns User information along with access and refresh tokens.
    """
    user = CustomUser.objects.filter(email=email)
    if user.exists():
        return login_google_user(email)
    else:
        new_user = {
            'email': email,
            'username': username,
            'password': settings.CUSTOM_PASSWORD_FOR_AUTH
        }
        register_user = CustomUser.objects.create_user(**new_user)
        register_user.is_active = True
        register_user.save()
        return login_google_user(email)
        

#phone number login utilities

def generate_otp():
    """
    Generate a random 6-digit OTP.

    Returns Randomly generated OTP.
    """
    return ''.join(random.choices('0123456789', k=6))

def send_otp(phone_number, otp):   
    """
    Send OTP to the given phone number.
    """
    message = f'Hello {otp}, This is a test message from spring edge '
    mobileno= phone_number
    sender = 'SEDEMO'
    apikey = '621492a44a89m36c2209zs4l7e74672cj'

    baseurl = 'https://instantalerts.co/api/web/send/?apikey='+apikey
    url= baseurl+'&sender='+sender+'&to='+mobileno+'&message='+message+'&format=json'
    response = req.get(url)

# def send_otp(phone_number, otp):
#     """
#     voice msg of OTP to the given Phone number
#     """

#     url = f"https://2factor.in/API/V1/{settings.SMS_API_KEY}/SMS/{phone_number}/{otp}/OTP1"

#     payload={}
#     headers = {}

#     response = requests.request("GET", url, headers=headers, data=payload)
#     print(response.text)

def create_Mobile_user(phone_number, otp):
    """
    Create or retrieve a user using the provided phone number and OTP.
 
    Returns CustomUser User object if created or retrieved successfully.

    Raises ValidationError If OTP is invalid or has expired.
    """
    user = CustomUser.objects.filter(phone_number=phone_number).first()
    if user:
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        return user    
    else:
        # If user doesn't exist, create new one
        new_user = CustomUser.objects.create_phone_user(
            phone_number=phone_number,
            password=settings.CUSTOM_PASSWORD_FOR_AUTH
        )
        new_user.is_active = True
        new_user.save(update_fields=['is_active'])
        return new_user

def create_email_user(email):
    """
    Create or retrieve a user using the provided email and OTP.

    Returns CustomUser: User object if created or retrieved successfully.

    Raises ValidationError: If OTP is invalid or has expired.
    """

    user = CustomUser.objects.filter(email=email).first()
    if user:
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        return user
    else:
        username = email.split('@')[0] 
        new_user = CustomUser.objects.create_user(
            email=email, username=username,
            password=settings.CUSTOM_PASSWORD_FOR_AUTH
        )
        new_user.is_active = True
        new_user.save(update_fields=['is_active'])
        return new_user   


def validate_and_format_phone_number(phone_number):
    """
    Validate and format the phone number using phonenumbers library.
    Returns the formatted phone number or raises a validation error.
    """
    try:
        print('entered in validating phone-number')
        parsed_number = phonenumbers.parse(phone_number, None)
        if not phonenumbers.is_valid_number(parsed_number):
            raise serializers.ValidationError(constants.ERROR_INVALID_FORMAT)
        
        formatted_number = phonenumbers.format_number(
            parsed_number,
            phonenumbers.PhoneNumberFormat.E164
        )
        return formatted_number
    except NumberParseException:
        raise serializers.ValidationError(constants.INVALID_PHONE_NUMBER)

