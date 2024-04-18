from django.db import models
from customadmin.models import Location, Category
import uuid
from accounts.models import CustomUser

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
    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='event_tickets'
    )
    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    unique_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    def __str__(self):
        return f"{self.ticket_type.type_name} - {self.unique_code}"
    
class Event(models.Model):
    event_name = models.CharField(max_length=255)
    categories = models.ManyToManyField(Category, related_name='events')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
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
    event_img_1 = models.ImageField(upload_to='event_images/',null=True, blank=True)
    event_img_2 = models.ImageField(upload_to='event_images/', null=True, blank=True)
    event_img_3 = models.ImageField(upload_to='event_images/', null=True, blank=True)
    about = models.TextField()
    instruction = models.TextField(null=True, blank=True)
    terms_and_conditions = models.TextField()
    vendor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='events')

    def __str__(self):
        return self.event_name

