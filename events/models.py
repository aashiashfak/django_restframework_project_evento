from django.db import models
from customadmin.models import Location, Category
from vendors.models import Vendor
import uuid

class Venue(models.Model):
    name = models.CharField(max_length=255)
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='venues'
    )

    def __str__(self):
        return self.name

class TicketType(models.Model):
    type_name = models.CharField(max_length=255, unique=True)
    count = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    ticket_image = models.ImageField(upload_to='ticket_images/')
    sold_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.type_name
    
class Ticket(models.Model):
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
    event_img_1 = models.ImageField(upload_to='event_images/')
    event_img_2 = models.ImageField(upload_to='event_images/', null=True, blank=True)
    event_img_3 = models.ImageField(upload_to='event_images/', null=True, blank=True)
    about = models.TextField()
    instruction = models.TextField(null=True, blank=True)
    terms_and_conditions = models.TextField()
    tickets = models.ManyToManyField(TicketType, related_name='events')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='events')

    def __str__(self):
        return self.event_name
