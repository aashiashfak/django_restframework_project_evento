from django.db import models

from django.db import models
from django.db import models

class Vendor(models.Model):
    organizer_name = models.CharField(max_length=255, unique=True)
    pan_card_number = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    GSTIN = models.BooleanField(default=False)
    ITR = models.BooleanField(default=False)
    contact_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    benificiary_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    IFSC_code = models.CharField(max_length=20)
    is_vendor = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.organizer_name

