from django.contrib import admin
from .models import Category,Location,Banner

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    
    list_display = ['id', 'name', 'image'] 


class LocationAdmin(admin.ModelAdmin):
    
    list_display = ['id', 'name'] 

class BannerAdmin(admin.ModelAdmin):
    
    list_display = ['id','image','description']

admin.site.register(Category,UserAdmin)
admin.site.register(Location,LocationAdmin)
admin.site.register(Banner,BannerAdmin)
