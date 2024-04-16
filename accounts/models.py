from django.db import models 
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from django.db import models
from .manager import CustomUserManager
from django.core.validators import EmailValidator
from django.conf import settings




email_validator = EmailValidator()

 


class CustomUser(AbstractBaseUser,PermissionsMixin):
    
    username= models.CharField(max_length=70, unique=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    email = models.EmailField(max_length=255, unique=True, null=True,validators=[email_validator])
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login  = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False) 
    is_vendor = models.BooleanField(default=False) 

    # vendor_id = 
   
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

# class VendorDetails(models.Model):

    objects = CustomUserManager()

    def __str__(self):
        if self.username:
            return self.username
        else:
            return str(self.id)  
    

class PendingUser(models.Model):
    """
    Model for pending users awaiting verification.
    """
    phone_number = models.CharField(max_length=15, null=True)
    otp = models.CharField(max_length=6)
    expiry_time = models.DateTimeField()
    email= models.EmailField(max_length=255, null=True)

    





