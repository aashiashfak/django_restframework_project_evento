from django.contrib import admin
from .models import CustomUser,PendingUser

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(PendingUser)