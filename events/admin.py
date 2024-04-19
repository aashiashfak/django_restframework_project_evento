from django.contrib import admin
from .models import Event, TicketType, Venue, Ticket
# from customadmin.models import Location

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ['type_name', 'ticket_image', 'price', 'count','sold_count', 'event']
    search_fields = ['type_name']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_type', 'event', 'unique_code']
    search_fields = ['ticket_type__type_name', 'event__event_name']
    list_filter = ['ticket_type', 'event']

class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 0

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'event_name', 'start_date', 'end_date', 'venue', 'location', 'vendor', 'display_categories']
    search_fields = ['event_name', 'venue__name', 'vendor__username']
    list_filter = ['vendor']
    inlines = [TicketTypeInline]

    def display_categories(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])

    display_categories.short_description = "Categories"
