from django.contrib import admin
from .models import Vendor
# Register your models here.

class UserAdmin(admin.ModelAdmin):

    list_display = ('organizer_name', 'pan_card_number', 'contact_name', 'email', 'phone_number', 'is_vendor', 'is_active')
    list_filter = ('is_vendor', 'is_active')
    search_fields = ('organizer_name', 'contact_name', 'email', 'phone_number')

admin.site.register(Vendor,UserAdmin)

