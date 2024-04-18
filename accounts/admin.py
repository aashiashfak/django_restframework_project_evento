from django.contrib import admin
from .models import CustomUser,PendingUser,Vendor

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'phone_number', 'date_joined', 'last_login', 'is_staff', 'is_superuser', 'is_active'] 


admin.site.register(CustomUser)
admin.site.register(PendingUser)
admin.site.register(Vendor)