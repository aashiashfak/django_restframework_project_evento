import datetime
from rest_framework import serializers
from .models import Event, TicketType, Venue, Ticket, WishList
from customadmin.models import Category, Location
from django.utils.translation import gettext_lazy as _
from accounts.models import Vendor, CustomUser
from .utilities import generate_qr_code
from django.utils import timezone
from django.db.models import Sum
from accounts import constants
from customadmin.utilities import cached_queryset

class TicketTypeSerializer(serializers.ModelSerializer):

    sold_count = serializers.IntegerField(required=False, allow_null=True)
    class Meta:
        model = TicketType
        fields = ['id', 'type_name', 'price', 'count', 'sold_count', 'ticket_image']
        read_only_fields = ['id']



class TicketTypeCreateSerializer(serializers.ModelSerializer):
    sold_count = serializers.IntegerField(required=False, allow_null=True)
    event = serializers.SlugRelatedField(slug_field='event_name', queryset=Event.objects.all())
    id = serializers.ReadOnlyField()
    count = serializers.IntegerField(required=True)

    class Meta:
        model = TicketType
        fields = ['id', 'type_name', 'ticket_image', 'price', 'count', 'sold_count', 'event']

    def validate(self, data):
        errors = {}

        request = self.context.get('request')
        if request and request.method == 'POST':
            event_name = data.get('event')
            try:
                event = Event.objects.get(event_name=event_name)
                data['event'] = event  # Replace event_name with the actual event object
            except Event.DoesNotExist:
                errors['event'] = "Event with the provided name does not exist."

        # Validate sold_count
        sold_count = data.get('sold_count')
        count = data.get('count') or (self.instance and self.instance.count)

        
        if sold_count is not None and count is not None and sold_count > count:
            errors['sold_count'] = "Sold count cannot be greater than total count."

        if errors:
            raise serializers.ValidationError(errors)

        return data



class EventCreateSerializer(serializers.Serializer):

    venue = serializers.CharField(max_length=255, required=False)  
    location = serializers.CharField(max_length=255, required=False)  
    categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
    )
    event_name = serializers.CharField(max_length=255, required=False)  
    time = serializers.TimeField(required=False) 
    start_date = serializers.DateTimeField(required=False)  
    end_date = serializers.DateTimeField(required=False) 
    event_img_1 = serializers.ImageField(required=False, allow_null=True)
    event_img_2 = serializers.ImageField(required=False, allow_null=True)
    event_img_3 = serializers.ImageField(required=False, allow_null=True)
    about = serializers.CharField(required=False)
    instruction = serializers.CharField(required=False, allow_blank=True)
    terms_and_conditions = serializers.CharField(required=False)
    ticket_types = TicketTypeSerializer(many=True, required=False)
    location_url = serializers.URLField(required=False)

    def validate(self, attrs):
        errors = {}

        venue_name = attrs.get('venue')
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        event_name = attrs.get('event_name')

        print('attrs:...........................................',attrs)

        # Validation logic for venue availability and event name - 
        if venue_name and start_date and end_date:
            if Event.objects.filter(venue__name=venue_name, start_date__lte=end_date, end_date__gte=start_date).exists():
                print('hai....................................................................................')
                errors['venue'] = "The venue is already booked for the specified date range."

        if event_name and Event.objects.filter(event_name=event_name).exists():
            errors['event_name'] = "An event with the same name already exists."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    
    def validate_location(self, value):
        try:
            Location.objects.get(name=value)
        except Location.DoesNotExist:
            raise serializers.ValidationError("Location not found.")
        return value
    
    def create(self, validated_data):
        venue_name = validated_data.pop('venue')
        location_name = validated_data.pop('location')
        categories_data = validated_data.pop('categories', [])
        ticket_types_data = validated_data.pop('ticket_types')

        try:
            with transaction.atomic():
                # Create or get venue and location - This part ensures venue and location are correctly linked
                venue, _ = Venue.objects.get_or_create(name=venue_name)
                location = Location.objects.get(name=location_name)

                validated_data['venue'] = venue
                validated_data['location'] = location

                # Create event
                event = Event.objects.create(**validated_data)

                # Handle categories - This section is refactored to correctly set categories
                categories = []
                for category_name in categories_data:
                    category = Category.objects.get(name=category_name)
                    categories.append(category)
                event.categories.set(categories)  # Set categories correctly

                # Handle ticket types - This section is refactored to correctly create ticket types
                for ticket_type_data in ticket_types_data:
                    TicketType.objects.create(event=event, **ticket_type_data)

                # Return the serialized event with explicit categories and ticket types - Modified return structure
                event_data = {
                    'id': event.id,
                    'venue': event.venue.name,
                    'location': event.location.name,
                    'categories': [category.name for category in categories],  # Convert categories to list of names
                    'event_name': event.event_name,
                    'time': event.time,
                    'start_date': event.start_date,
                    'location_url': event.location_url,
                    'end_date': event.end_date,
                    'event_img_1': event.event_img_1.url if event.event_img_1 else None,
                    'event_img_2': event.event_img_2.url if event.event_img_2 else None,
                    'event_img_3': event.event_img_3.url if event.event_img_3 else None,
                    'about': event.about,
                    'instruction': event.instruction,
                    'terms_and_conditions': event.terms_and_conditions,
                    'ticket_types': TicketTypeSerializer(event.ticket_types.all(), many=True).data,  # Serialize ticket types
                }
                print('event created succussfully........')

                return event_data

        except Exception as e:
            print('error while creating event_data',e)
            raise serializers.ValidationError(str(e))  # Improved error handling
    
    def update(self, instance, validated_data):
        print('Entered in event updating')

        # Extract fields from validated_data
        venue_name = validated_data.pop('venue', None)
        location_name = validated_data.pop('location', None)
        categories_data = validated_data.pop('categories', None)
        ticket_types_data = validated_data.pop('ticket_types', None)

        try:
            with transaction.atomic():
                # Update or get venue and location if provided
                if venue_name:
                    venue, _ = Venue.objects.get_or_create(name=venue_name)
                    instance.venue = venue
                    print(f"Venue set to: {venue.name}")

                if location_name:
                    location, _ = Location.objects.get_or_create(name=location_name)
                    instance.location = location
                    print(f"Location set to: {location.name}")

                # Update event fields
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                    print(f"Set {attr} to {value}")

                print('Basic event fields updated successfully')

                # Update categories if provided
                if categories_data is not None:
                    current_categories = set(instance.categories.values_list('name', flat=True))
                    new_categories = set(categories_data)

                    # Categories to remove
                    categories_to_remove = current_categories - new_categories
                    if categories_to_remove:
                        instance.categories.filter(name__in=categories_to_remove).delete()
                        print(f"Removed categories: {categories_to_remove}")

                    # Categories to add
                    categories_to_add = new_categories - current_categories
                    if categories_to_add:
                        categories = [Category.objects.get_or_create(name=category_name)[0] for category_name in categories_to_add]
                        instance.categories.add(*categories)
                        print(f"Added categories: {categories_to_add}")

                print('Categories updated successfully')

                # Update ticket types if provided
                if ticket_types_data is not None:
                    existing_ticket_types = {ticket_type.type_name: ticket_type for ticket_type in instance.ticket_types.all()}
                    print(f"Existing ticket types: {list(existing_ticket_types.keys())}")

                    for ticket_type_data in ticket_types_data:
                        type_name = ticket_type_data.get('type_name')
                        print(f"Processing ticket type: {type_name}")

                        if type_name in existing_ticket_types:
                            # Update existing ticket type if any changes are detected
                            ticket_type = existing_ticket_types.pop(type_name)
                            updated = False

                            for attr, value in ticket_type_data.items():
                                if getattr(ticket_type, attr) != value:
                                    setattr(ticket_type, attr, value)
                                    updated = True
                                    print(f"Updated {attr} for ticket type '{type_name}' to {value}")

                            if updated:
                                ticket_type.save()
                                print(f"Ticket type '{type_name}' updated successfully")
                            else:
                                print(f"No changes detected for ticket type '{type_name}'")

                        else:
                            # Create new ticket type if it doesn't exist
                            TicketType.objects.create(event=instance, **ticket_type_data)
                            print(f"Created new ticket type: {type_name}")

                    # Remove any ticket types that were not included in the update
                    if existing_ticket_types:
                        removed_ticket_types = list(existing_ticket_types.keys())
                        TicketType.objects.filter(type_name__in=removed_ticket_types).delete()
                        print(f"Removed ticket types: {removed_ticket_types}")

                print('Ticket types updated successfully')

                # Save the instance
                instance.save()
                print("Event instance saved successfully")
            return instance

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise serializers.ValidationError(str(e))



        
        
class EventUpdateSerializer(serializers.Serializer):
    venue = serializers.CharField(max_length=255, required=True)
    location = serializers.CharField(max_length=255, required=False)
    categories = serializers.ListSerializer(child=serializers.CharField(), required=False)
    event_name = serializers.CharField(max_length=255, required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    time = serializers.TimeField(required=True)
    event_img_1 = serializers.ImageField(required=False)
    event_img_2 = serializers.ImageField(required=False, allow_null=True)
    event_img_3 = serializers.ImageField(required=False, allow_null=True)
    about = serializers.CharField(required=False)
    instruction = serializers.CharField(required=False, allow_blank=True)
    terms_and_conditions = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=Event.STATUS_CHOICES)
    ticket_types = serializers.ListSerializer(child=TicketTypeSerializer())

    def validate(self, attrs):
        Venue_name = attrs.get('venue')
        categories_data = attrs.get('categories', [])
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        location_name = attrs.get('location')

        if location_name:
            try:
                location = Location.objects.get(name=location_name)
                attrs['location'] = location
            except Location.DoesNotExist:
                raise serializers.ValidationError(constants.ERROR_LOCATION_NOT_FOUND)

        if Venue_name:
            venue, _ = Location.objects.get_or_create(name=Venue_name)
            attrs['venue'] = venue

        # Check if categories exist
        for category_name in categories_data:
            try:
                category = Category.objects.get(name=category_name)
            except Category.DoesNotExist:
                raise serializers.ValidationError(f"Category '{category_name}' does not exist.")

        # Check if the venue is already booked for the specified date range
        if Venue_name and (start_date or end_date):
            if Event.objects.filter(venue=venue, start_date__lte=end_date, end_date__gte=start_date).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError(_(constants.ERROR_VENUE_BOOKED))

        return attrs

    def update(self, instance, validated_data):
        instance.location = validated_data.get('location', instance.location)
        instance.event_name = validated_data.get('event_name', instance.event_name)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.event_img_1 = validated_data.get('event_img_1', instance.event_img_1)
        instance.event_img_2 = validated_data.get('event_img_2', instance.event_img_2)
        instance.event_img_3 = validated_data.get('event_img_3', instance.event_img_3)
        instance.about = validated_data.get('about', instance.about)
        instance.instruction = validated_data.get('instruction', instance.instruction)
        instance.terms_and_conditions = validated_data.get('terms_and_conditions', instance.terms_and_conditions)
        instance.status = validated_data.get('status', instance.status) 
        instance.save()

        # Clear existing categories and add new ones
        categories_data = validated_data.get('categories', [])
        for category_name in categories_data:
            category = Category.objects.get(name=category_name)
            instance.categories.add(category)

        

        return instance



class EventSerializer(serializers.ModelSerializer):
    print('enterd in eventSerializer')
    organizer_name = serializers.CharField(source='vendor.vendor_details.organizer_name', read_only=True)
    organizer_email = serializers.CharField(source='vendor.email', read_only=True)
    organizer_phone = serializers.CharField(source='vendor.phone_number', read_only=True)
    organizer_id = serializers.CharField(source='vendor.vendor_details.id', read_only=True)
    organizer_profile_photo = serializers.CharField(source='vendor.profile_picture', read_only=True)
    categories = serializers.SlugRelatedField(slug_field='name', queryset=Category.objects.all(), many=True)
    # venue = serializers.SlugRelatedField(slug_field='name', queryset=Venue.objects.all())
    venue = serializers.CharField()
    location = serializers.SlugRelatedField(slug_field='name', queryset=Location.objects.all())
    vendor = serializers.SerializerMethodField()
    ticket_types = TicketTypeSerializer(many=True)

    class Meta:
        model = Event
        fields = [
            'id', 'event_name', 'categories', 'start_date', 'end_date', 'time', 'venue', 'location', 'event_img_1',
            'event_img_2', 'event_img_3', 'about', 'instruction', 'terms_and_conditions', 'vendor', 'status',
            'location_url', 'organizer_id', 'organizer_name', 'organizer_email', 'organizer_phone', 'organizer_profile_photo', 'ticket_types',
        ]

    def validate(self, attrs):
        errors = {}
        print('entered in validation')

        venue_name = attrs.get('venue')
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        event_name = attrs.get('event_name')

        print('attrs:...........................................', attrs)

        
        if venue_name and start_date and end_date:
            if Event.objects.filter(venue__name=venue_name, start_date__lte=end_date, end_date__gte=start_date).exists():
                print('hai....................................................................................')
                errors['venue'] = "The venue is already booked for the specified date range."

        if event_name and Event.objects.filter(event_name=event_name).exists():
            errors['event_name'] = "An event with the same name already exists."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    
    def validate_location(self, value):
        try:
            Location.objects.get(name=value)
        except Location.DoesNotExist:
            raise serializers.ValidationError("Location not found.")
        return value
    
    def create(self, validated_data):
        venue_name = validated_data.pop('venue')
        location_name = validated_data.pop('location')
        categories_data = validated_data.pop('categories', [])
        ticket_types_data = validated_data.pop('ticket_types')

        try:
            with transaction.atomic():
                # Create or get venue and location - This part ensures venue and location are correctly linked
                print('venue:........................',venue_name)
                venue, created = Venue.objects.get_or_create(name=venue_name)
                if created:
                    print(f"Created new venue: {venue.name}")
               
                location = Location.objects.get(name=location_name)

                validated_data['venue'] = venue
                validated_data['location'] = location

                # Create event
                event = Event.objects.create(**validated_data)

                # Handle categories - This section is refactored to correctly set categories
                categories = []
                for category_name in categories_data:
                    category = Category.objects.get(name=category_name)
                    categories.append(category)
                event.categories.set(categories)  # Set categories correctly

                # Handle ticket types - This section is refactored to correctly create ticket types
                for ticket_type_data in ticket_types_data:
                    TicketType.objects.create(event=event, **ticket_type_data)

                return event

        except Exception as e:
            print('error while creating event_data',e)
            raise serializers.ValidationError(str(e))  # Improved error handling
    
    def update(self, instance, validated_data):
        print('Entered in event updating')

        # Extract fields from validated_data
        venue_name = validated_data.pop('venue', None)
        location_name = validated_data.pop('location', None)
        categories_data = validated_data.pop('categories', None)
        # ticket_types_data = validated_data.pop('ticket_types', None)

        try:
            with transaction.atomic():
                # Update or get venue and location if provided
                if venue_name:
                    venue, _ = Venue.objects.get_or_create(name=venue_name)
                    instance.venue = venue
                    print(f"Venue set to: {venue.name}")

                if location_name:
                    location, _ = Location.objects.get_or_create(name=location_name)
                    instance.location = location
                    print(f"Location set to: {location.name}")

                # Update event fields
                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                    print(f"Set {attr} to {value}")

                print('Basic event fields updated successfully')

                # Update categories if provided
                if categories_data is not None:
                    current_categories = set(instance.categories.values_list('name', flat=True))
                    new_categories = set(categories_data)

                    # Categories to remove
                    categories_to_remove = current_categories - new_categories
                    if categories_to_remove:
                        instance.categories.filter(name__in=categories_to_remove).delete()
                        print(f"Removed categories: {categories_to_remove}")

                    # Categories to add
                    categories_to_add = new_categories - current_categories
                    if categories_to_add:
                        categories = [Category.objects.get_or_create(name=category_name)[0] for category_name in categories_to_add]
                        instance.categories.add(*categories)
                        print(f"Added categories: {categories_to_add}")

                print('Categories updated successfully')

                # Save the instance
                instance.save()
                print("Event instance saved successfully")
            return instance

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise serializers.ValidationError(str(e))

    def get_vendor(self, obj):

        if obj.vendor:
            return obj.vendor.username if obj.vendor.username else obj.vendor.id
        return None


class WishListSerializer(serializers.ModelSerializer):
    """
    Serializer for WishList model.
    """
    event = EventSerializer(read_only=True)

    class Meta:
        model = WishList
        fields = ['id', 'user', 'event', 'added_at']

    def create(self, validated_data):
        """
        Custom create method to handle adding events to user's wish list.
        """
        user = self.context['request'].user
        event_id = self.context['event_id']
        
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event does not exist")
        
        existing_wishlist = WishList.objects.filter(user=user, event=event)
        if existing_wishlist.exists():
            raise serializers.ValidationError("Event already exists in wishlist")
        
        wishlist = WishList.objects.create(user=user, event=event)
        return wishlist



from django.db import transaction

class TicketBookingSerializer(serializers.ModelSerializer):
    ticket_count = serializers.IntegerField(min_value=1, required=True)

    class Meta:
        model = Ticket
        fields = ['ticket_count']

    def validate(self, attrs):
        ticket_count = attrs['ticket_count']
        ticket_type = self.context['ticket_type']

        if ticket_type.event.status != 'active':
            raise serializers.ValidationError("Event is not currently active.")

        # Check if there are enough available tickets before booking
        available_tickets = ticket_type.count - ticket_type.sold_count
        if ticket_count > available_tickets:
            raise serializers.ValidationError("Not enough tickets available.")
        
        if ticket_count > 5:
            raise serializers.ValidationError("Cannot book more than 5 tickets.")

        return attrs




class PaymentConfirmationSerializer(serializers.ModelSerializer):
    event_name = serializers.ReadOnlyField(source='ticket_type.event.event_name')
    event_date = serializers.ReadOnlyField(source='ticket_type.event.start_date')
    ticket_type_name = serializers.ReadOnlyField(source='ticket_type.type_name')
    quantity = serializers.ReadOnlyField(source='ticket_count')
    total_price = serializers.ReadOnlyField(source='ticket_price')
   

    class Meta:
        model = Ticket
        fields = [
            'event_name', 'event_date', 'ticket_type_name', 'quantity', 'total_price']



class TicketSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='ticket_type.event.vendor.vendor_details.organizer_name', read_only=True)
    event_name = serializers.CharField(source='ticket_type.event', read_only=True)
    type_name = serializers.CharField(source='ticket_type.type_name', read_only=True)
    event_date = serializers.DateTimeField(source='ticket_type.event.start_date',read_only=True)


    class Meta:
        model = Ticket
        fields = '__all__' 
        extra_fields = ['organizer_name', 'event_name', 'type_name', 'event_date']

from django.db.models import Sum

class TrendingEventSerializer(serializers.ModelSerializer):
    """
    Serializer for trending events based on total quantity of active tickets in the last 30 days.
    """

    total_active_ticket_quantity = serializers.IntegerField()
    organizer_name = serializers.SerializerMethodField()
    categories = serializers.StringRelatedField(many=True)
    venue = serializers.StringRelatedField()
    location = serializers.StringRelatedField()
    ticket_types  = TicketTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'event_name', 'total_active_ticket_quantity', 'categories', 'start_date', 'time', 'end_date', 'venue', 'location', 'event_img_1',
            'event_img_2', 'event_img_3', 'about', 'instruction', 'terms_and_conditions', 'status', 'ticket_types',
            'organizer_name',
        ]

    def get_organizer_name(self, obj):
        return obj.vendor.vendor_details.organizer_name

    @staticmethod
    def get_trending_events():
        # Calculate the start date for the last 30 days
        last_thirty_day = timezone.now() - timezone.timedelta(days=30)

        # Fetch the top trending active events in the last 30 days
        trending_events = Event.objects.filter(
                    status='active',
                    ticket_types__tickets__booking_date__gte=last_thirty_day,
                    ticket_types__tickets__ticket_status='active'  # Filter tickets with active status
                ).select_related(
                    'venue',
                    'location',
                    'vendor__vendor_details__user'
                ).prefetch_related(
                    'categories',
                ).annotate(
                    total_active_ticket_quantity=Sum('ticket_types__tickets__ticket_count')
                ).order_by('-total_active_ticket_quantity')[:10]
        

        return trending_events



class UserTicketDetailsSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    phone_number = serializers.CharField(source='user.phone_number')
    ticket_type_name = serializers.CharField(source='ticket_type.type_name')
    event_name = serializers.CharField(source='ticket_type.event.event_name')
    

    class Meta:
        model = Ticket
        fields = [
            'id', 'username', 'email', 'phone_number', 'ticket_price', 'ticket_count',
            'ticket_type_name', 'event_name', 'ticket_status'
        ]



#event retrieve serializer -------

# class EventRetrieveSerializer(serializers.ModelSerializer):
#     ticket_types = serializers.SerializerMethodField()

#     class Meta:
#         model = Event
#         fields = '__all__'

#     def get_ticket_types(self, obj):
#         ticket_types_data = TicketTypeSerializer(obj.ticket_types, many=True).data
#         return ticket_types_data




# from rest_framework import serializers
# from .models import Event, TicketType, Venue, Ticket
# from customadmin.models import Category,Location

# class LocationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Location
#         fields = '__all__'

# class VenueSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Venue
#         fields = '__all__'


# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = '__all__'



# class EventSerializer(serializers.ModelSerializer):
#     venue = VenueSerializer()
#     location = LocationSerializer()
#     categories = serializers.ListSerializer(child=serializers.CharField())

#     # Define ticket type fields directly within the EventSerializer
#     ticket_types = serializers.ListSerializer(child=serializers.DictField(child=serializers.CharField()))

#     class Meta:
#         model = Event
#         exclude = ['vendor']

#     def create(self, validated_data):
#         venue_data = validated_data.pop('venue')
#         location_data = validated_data.pop('location', None)
#         categories_data = validated_data.pop('categories')
#         ticket_types_data = validated_data.pop('ticket_types')

#         venue, _ = Venue.objects.get_or_create(name=venue_data['name'])

#         if location_data:
#             location_name = location_data['name']
#             location, created = Location.objects.get_or_create(name=location_name)
#         else:
#             location = None

#         event = Event.objects.create(venue=venue, location=location, **validated_data)

#         for category_name in categories_data:
#             try:
#                 category = Category.objects.get(name=category_name)
#             except Category.DoesNotExist:
#                 raise serializers.ValidationError(f"Category '{category_name}' does not exist.")

#             event.categories.add(category)

#         for ticket_type_data in ticket_types_data:
#             # Create TicketType instances for each ticket type data
#             TicketType.objects.create(event=event, **ticket_type_data)

#         return event

#     def update(self, instance, validated_data):
#         venue_data = validated_data.pop('venue')
#         location_name = validated_data.pop('location.name', None)
#         categories_data = validated_data.pop('categories', [])
#         ticket_types_data = validated_data.pop('ticket_types', [])

#         venue, _ = Venue.objects.get_or_create(name=venue_data['name'])

#         if location_name:
#             location, _ = Location.objects.get_or_create(name=location_name)
#             instance.location = location

#         instance.event_name = validated_data.get('event_name', instance.event_name)
#         instance.start_date = validated_data.get('start_date', instance.start_date)
#         instance.end_date = validated_data.get('end_date', instance.end_date)
#         instance.event_img_1 = validated_data.get('event_img_1', instance.event_img_1)
#         instance.event_img_2 = validated_data.get('event_img_2', instance.event_img_2)
#         instance.event_img_3 = validated_data.get('event_img_3', instance.event_img_3)
#         instance.about = validated_data.get('about', instance.about)
#         instance.instruction = validated_data.get('instruction', instance.instruction)
#         instance.terms_and_conditions = validated_data.get('terms_and_conditions', instance.terms_and_conditions)

#         instance.venue = venue
#         instance.save()

#         instance.categories.clear()

#         for category_name in categories_data:
#             try:
#                 category = Category.objects.get(name=category_name)
#             except Category.DoesNotExist:
#                 raise serializers.ValidationError(f"Category '{category_name}' does not exist.")

#             instance.categories.add(category)

#         # Delete existing TicketType instances
#         instance.ticket_types.all().delete()

#         for ticket_type_data in ticket_types_data:
#             # Create TicketType instances for each ticket type data
#             TicketType.objects.create(event=instance, **ticket_type_data)

#         return instance





# from rest_framework import serializers
# from .models import Event, TicketType, Venue, Ticket
# from customadmin.models import Category, Location

# class TicketTypeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TicketType
#         fields = '__all__'

# class VenueSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Venue
#         fields = '__all__'

# class EventSerializer(serializers.ModelSerializer):
#     ticket_types = TicketTypeSerializer(many=True, read_only=True)
#     venue = serializers.PrimaryKeyRelatedField(queryset=Venue.objects.all(), allow_null=True, required=False)
#     location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all(), allow_null=True, required=False)

#     class Meta:
#         model = Event
#         fields = (
#             'event_name', 'categories', 'start_date', 'end_date', 'venue', 'location',
#             'event_img_1', 'event_img_2', 'event_img_3', 'about', 'instruction',
#             'terms_and_conditions', 'vendor'
#         )
        

#     def create(self, validated_data):
#         ticket_types_data = validated_data.pop('ticket_types')
#         categories = validated_data.pop('categories')

#         # Create event
#         event = Event.objects.create(**validated_data)

#         # Set categories
#         event.categories.set(categories)

#         # Create ticket types and tickets
#         for ticket_type_data in ticket_types_data:
#             ticket_type = TicketType.objects.create(event=event, **ticket_type_data)

#         return event

   