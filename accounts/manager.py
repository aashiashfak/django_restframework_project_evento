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
        user.save(using=self._db)
        return user


    def create_phone_user(self, phone_number, password):
        """ 
        Creates and saves a User with the given phone_number and password
        """
        if not phone_number:
            raise ValueError('The phone_number field must be set')
        user = self.model(phone_number=phone_number)
        user.set_password(password)  
        user.save(using=self._db)  
        return user  



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
