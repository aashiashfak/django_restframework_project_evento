from django.db import models 
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from django.db import models
from .manager import CustomUserManager
from django.core.validators import RegexValidator
from django.conf import settings



phone_regex = RegexValidator(
    regex=r'^\d{10}',message='phone number must be 10 digits only.'
)
 


class CustomUser(AbstractBaseUser,PermissionsMixin):
    # Define model fields
    username= models.CharField(max_length=70, unique=True, null=True)
    email = models.EmailField(max_length=255, unique=True, null=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login  = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False) 
   
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        if self.username:
            return self.username
        else:
            return str(self.id)  
    

class PendingUser(models.Model):
    phone_number = models.CharField(max_length=15, null=True)
    otp = models.CharField(max_length=6)
    expiry_time = models.DateTimeField()
    email= models.EmailField(max_length=255, null=True)

    

