from django.contrib import admin
from .models import CustomUser,PendingUser,Vendor,Follow

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ['id','username', 'email', 'phone_number', 'date_joined', 'last_login', 'is_vendor', 'is_superuser', 'is_active'] 

class FollowAdmin(admin.ModelAdmin):
    list_display = ['id','follower','vendor','created_at' ]

class VendorAdmin(admin.ModelAdmin):
    list_display = ['id','organizer_name', 'user']

admin.site.register(CustomUser,UserAdmin)
admin.site.register(PendingUser)
admin.site.register(Follow,FollowAdmin)
admin.site.register(Vendor,VendorAdmin)