from django.contrib import admin
from .models import Event, TicketType, Venue, Ticket, Payment, WishList
# from customadmin.models import Location

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ['id','type_name', 'ticket_image', 'price', 'count','sold_count', 'event']
    search_fields = ['type_name']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket_type', 'event_name', 'user', 'ticket_price', 'ticket_count', 'booking_date', 'ticket_status']
    search_fields = ['ticket_type__type_name', 'ticket_type__event__event_name']  # Updated search fields
    list_filter = ['ticket_type']
    
    def event_name(self, obj):
        return obj.ticket_type.event.event_name
    event_name.admin_order_field = 'ticket_type__event__event_name'  
    event_name.short_description = 'Event Name'


class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 0

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'event_name', 'start_date', 'status', 'end_date', 'venue', 'location', 'vendor', 'display_categories']
    search_fields = ['event_name', 'venue__name', 'vendor__username']
    list_filter = ['vendor']
    inlines = [TicketTypeInline]



    def display_categories(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])

    display_categories.short_description = "Categories"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order_id']

@admin.register(WishList)
class WishListAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'event',]
