from django.contrib import admin
from .models import Category

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ['name', 'image'] 


admin.site.register(Category,UserAdmin)
