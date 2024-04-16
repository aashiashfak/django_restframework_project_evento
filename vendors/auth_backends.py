
from django.contrib.auth.backends import ModelBackend
from .models import Vendor

class VendorAuthBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            vendor = Vendor.objects.get(email=email)
            if vendor.check_password(password):
                return vendor
        except Vendor.DoesNotExist:
            return None
