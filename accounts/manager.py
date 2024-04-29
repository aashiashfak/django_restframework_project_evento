from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, password=password, **extra_fields)
        user.set_password(password) 
        user.save()
        return user


    def create_phone_user(self, phone_number, password, **extra_fields):
        """ 
        Creates and saves a User with the given phone_number and password
        """
        if not phone_number:
            raise ValueError('The phone_number field must be set')
        user = self.model(phone_number=phone_number)
        user.set_password(password)  
        user.save()  
        return user  

    # def create_vendor_user_manager(self , email, password,  **extra_fields):
    #     if not email:
    #         raise ValueError('The Email field must be set')
        

    #     email = self.normalize_email(email)
    #     user = self.model(email=email, password=password, **extra_fields)
    #     user.set_password(password) 
    #     user.save()

    #     return user


    def create_superuser(self, username, email, password, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


# from django.contrib.auth.hashers import make_password
# from django.db import models

# class VendorManager(models.Manager):
#     def create_vendor_user(self, vendor_data, password):
#         """
#         Creates and saves a Vendor and CustomUser with the given data.
#         """
#         if not vendor_data.get('email'):
#             raise ValueError('The Email field must be set')
        
#         # Extract vendor-specific data
#         vendor_specific_data = {
#             'organizer_name': vendor_data.pop('organizer_name'),
#             'pan_card_number': vendor_data.pop('pan_card_number'),
#             'address': vendor_data.pop('address'),
#             'contact_name': vendor_data.pop('contact_name'),
#             'benificiary_name': vendor_data.pop('benificiary_name'),
#             'account_type': vendor_data.pop('account_type'),
#             'bank_name': vendor_data.pop('bank_name'),
#             'account_number': vendor_data.pop('account_number'),
#             'IFSC_code': vendor_data.pop('IFSC_code'),
#         }
        
#         # Create Vendor
#         vendor = Vendor.objects.create(**vendor_specific_data)
        
#         # Hashing password
#         hashed_password = make_password(password)
        
#         # Create CustomUser
#         user = CustomUser.objects.create_user(email=vendor_data['email'], password=hashed_password, vendor_id=vendor.id, **vendor_data)
        
#         return user, vendor



