from django.db import models 
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from django.db import models
from .manager import CustomUserManager
from django.core.validators import EmailValidator
from django.conf import settings



from rest_framework_simplejwt.tokens import RefreshToken



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

   
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

# class VendorDetails(models.Model):

    objects = CustomUserManager()


    @property
    def tokens(self) -> dict[str,str]:
        print('reached in gen tokens')
        
        referesh = RefreshToken.for_user(self)
        
        return{
           'refresh': str(referesh),
            'access': str(referesh.access_token),
        } 

    def __str__(self):
        if self.username:
            return self.username
        else:
            return str(self.id)  


class Vendor(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('current', 'Current Account'),
        ('saving', 'Savings Account'),
        ('joint', 'Joint Account'),
    ]

    organizer_name = models.CharField(max_length=255, unique=True)
    pan_card_number = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    GSTIN = models.BooleanField(default=False)
    ITR = models.BooleanField(default=False)
    contact_name = models.CharField(max_length=255)
    benificiary_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=100, choices=ACCOUNT_TYPE_CHOICES)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50, unique=True)
    IFSC_code = models.CharField(max_length=20)
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, null=True, blank=True,related_name='vendor_details')


    def __str__(self):
        return self.organizer_name
    
from django.contrib.auth.hashers import make_password

class VendorManager(models.Manager):
    
    def create_vendor_user(self, vendor_data, password):
        """
        Creates and saves a Vendor and CustomUser with the given data.
        """
        if not vendor_data.get('email'):
            raise ValueError('The Email field must be set')
        
        email = vendor_data.pop('email')
        
        # Extract vendor-specific data
        vendor_specific_data = {
            'organizer_name': vendor_data.pop('organizer_name'),
            'pan_card_number': vendor_data.pop('pan_card_number'),
            'address': vendor_data.pop('address'),
            'contact_name': vendor_data.pop('contact_name'),
            'benificiary_name': vendor_data.pop('benificiary_name'),
            'account_type': vendor_data.pop('account_type'),
            'bank_name': vendor_data.pop('bank_name'),
            'account_number': vendor_data.pop('account_number'),
            'IFSC_code': vendor_data.pop('IFSC_code'),
        }
        
        # Create Vendor
        vendor = Vendor.objects.create(**vendor_specific_data)

        
       
        
        username = email.split('@')[0] 
        # Create CustomUser
        user = CustomUser.objects.create_user(email=email, password=password, username=username, **vendor_data)
        user.is_vendor = True
        user.save(update_fields=['is_vendor'])
    
        
        # Associate user with vendor
        vendor.user = user
        vendor.save()
        return user, vendor
    
    

class PendingUser(models.Model):
    """
    Model for pending users awaiting verification.
    """
    phone_number = models.CharField(max_length=15, null=True)
    otp = models.CharField(max_length=6)
    expiry_time = models.DateTimeField()
    email= models.EmailField(max_length=255, null=True)




class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, related_name='following', on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'vendor') 

    def __str__(self):
        return f"{self.follower.username} follows {self.vendor.organizer_name}"








    





