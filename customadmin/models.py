from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='category_images', unique=True)

    def __str__(self) -> str:
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self) -> str:
        return self.name
    
class Banner(models.Model):
    image = models.ImageField(upload_to='banners')
    description = models.TextField()

    def __str__(self):
        return self.description[:50]