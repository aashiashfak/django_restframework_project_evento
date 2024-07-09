import datetime
from django.db import models
from customadmin.models import Location, Category
import uuid
from accounts.models import CustomUser
from django.core.cache import cache

class Venue(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class TicketType(models.Model):
    type_name = models.CharField(max_length=255)
    ticket_image = models.ImageField(upload_to='ticket_images/',null=True,blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    count = models.PositiveIntegerField(default=0)
    sold_count = models.PositiveIntegerField(default=0)
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='ticket_types')
    
    def __str__(self):
        return self.type_name


class Ticket(models.Model):
    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tickets')
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    ticket_count = models.PositiveIntegerField(default=1)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    TICKET_STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('used', 'Used'),
        ('pending','Pending'),
        ('disabled','Disabled')
    ]
    ticket_status = models.CharField(max_length=10, choices=TICKET_STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Ticket for {self.user} for event {self.ticket_type.event.event_name}"
    


    
    
class Event(models.Model):

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('disabled', 'Disabled'),
    )

    event_name = models.CharField(max_length=255)
    categories = models.ManyToManyField(Category, related_name='events')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    time = models.TimeField(default='17:00')
    venue = models.ForeignKey(
        Venue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    location = models.ForeignKey(
        'customadmin.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events'
    )
    location_url = models.URLField(max_length=200, null=True, blank=True, default=None)
    event_img_1 = models.ImageField(upload_to='event_images/',null=True, blank=True)
    event_img_2 = models.ImageField(upload_to='event_images/', null=True, blank=True)
    event_img_3 = models.ImageField(upload_to='event_images/', null=True, blank=True)
    about = models.TextField()
    instruction = models.TextField(null=True, blank=True)
    terms_and_conditions = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    vendor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='events')



    # def save(self, *args, **kwargs):
    #     if self.pk:
    #         original_event = Event.objects.get(pk=self.pk)
    #         if original_event.status != self.status:
    #             cache.delete('active_events')
    #     super().save(*args, **kwargs)
    

    def __str__(self):
        return self.event_name


class Payment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)


class WishList(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

