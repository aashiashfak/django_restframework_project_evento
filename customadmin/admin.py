from django.contrib import admin
from .models import Category,Location

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'image'] 


admin.site.register(Category,UserAdmin)
admin.site.register(Location)
