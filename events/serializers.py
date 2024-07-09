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
    sold_count = serializers.ReadOnlyField()
    event = serializers.PrimaryKeyRelatedField(read_only=True,)  
    id = serializers.ReadOnlyField()

    class Meta:
        model = TicketType
        fields = ['id', 'type_name', 'ticket_image', 'price', 'count', 'sold_count', 'event']



class TicketTypeCreateSerializer(serializers.ModelSerializer):
    sold_count = serializers.ReadOnlyField()
    event = serializers.SlugRelatedField(slug_field='event_name', queryset=Event.objects.all())
    id = serializers.ReadOnlyField()

    class Meta:
        model = TicketType
        fields = ['id', 'type_name', 'ticket_image', 'price', 'count', 'sold_count', 'event']

    def validate_event(self, value):
        try:
            event = Event.objects.get(event_name=value)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event with the provided name does not exist.")
        return event



class EventCreateSerializer(serializers.Serializer):
    venue = serializers.CharField(max_length=255, required=True)
    location = serializers.CharField(max_length=255, required=True)
    categories = serializers.ListSerializer(child=serializers.CharField())
    event_name = serializers.CharField(max_length=255)
    time = serializers.TimeField(required=True)
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    event_img_1 = serializers.ImageField(required=False, allow_null=True)
    event_img_2 = serializers.ImageField(required=False, allow_null=True)
    event_img_3 = serializers.ImageField(required=False, allow_null=True)
    about = serializers.CharField()
    instruction = serializers.CharField(required=False, allow_blank=True)
    terms_and_conditions = serializers.CharField()
    ticket_types = serializers.ListSerializer(child=TicketTypeSerializer())

   

    def validate(self, attrs):
        venue_name = attrs['venue']
        start_date = attrs['start_date']
        end_date = attrs['end_date']

        # Check if the venue is already booked for the specified date range
        if Event.objects.filter(venue__name=venue_name, start_date__lte=end_date, end_date__gte=start_date).exists():
            raise serializers.ValidationError(_(constants.ERROR_VENUE_BOOKED))

        # Check if an event with the same name already exists
        if Event.objects.filter(event_name=attrs['event_name']).exists():
            raise serializers.ValidationError(_(constants.ERROR_EVENT_EXISTS))

        return attrs

    def validate_categories(self, value):
        if not value:
            raise serializers.ValidationError(constants.ERROR_NO_CATEGORIES_PROVIDED)
        return value
    
    def validate_location(self, value):
        try:
            Location.objects.get(name=value)
        except Location.DoesNotExist:
            raise serializers.ValidationError(constants.ERROR_LOCATION_NOT_FOUND)
        return value
    

    def create(self, validated_data):
        venue_name = validated_data.pop('venue')
        location_name = validated_data.pop('location')
        categories_data = validated_data.pop('categories')
        ticket_types_data = validated_data.pop('ticket_types')
        

        venue, _ = Venue.objects.get_or_create(name=venue_name)

        location = Location.objects.get(name=location_name)

        validated_data['venue'] = venue
        validated_data['location'] = location
        

        # Create event
        event = Event.objects.create(**validated_data)

        # Set categories that the user entered
        if categories_data:
            for category_name in categories_data:
                try:
                    category = Category.objects.get(name=category_name)
                except Category.DoesNotExist:
                    raise serializers.ValidationError(f"Category '{category_name}' does not exist.")
                
                event.categories.add(category)
                
        # Create ticket types
        for ticket_type_data in ticket_types_data:
            ticket_type = TicketType.objects.create(
                event=event,
                **ticket_type_data
            )


        return event



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
    organizer_name = serializers.CharField(source='vendor.vendor_details.organizer_name', read_only=True)
    organizer_email = serializers.CharField(source='vendor.email', read_only=True)
    organizer_phone = serializers.CharField(source = 'vendor.phone_number',read_only=True)
    organizer_id = serializers.CharField(source = 'vendor.vendor_details.id',read_only=True)
    organizer_profile_photo = serializers.CharField(source = 'vendor.profile_picture',read_only=True)
    categories = serializers.StringRelatedField(many=True)
    venue = serializers.StringRelatedField()
    vendor = serializers.SerializerMethodField()
    location = serializers.StringRelatedField()
    ticket_types = TicketTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'event_name', 'categories', 'start_date', 'end_date', 'time', 'venue', 'location', 'event_img_1',
            'event_img_2', 'event_img_3', 'about', 'instruction', 'terms_and_conditions', 'vendor','status',
            'location_url', 'organizer_id', 'organizer_name', 'organizer_email', 'organizer_phone','organizer_profile_photo', 'ticket_types',
            ]

    # def get_organizer_name(self, obj):
    #     try:
    #         Custom_User = obj.vendor
    #         if Custom_User:
    #             vendor = Custom_User.vendor_details
    #             if vendor:
    #                 return vendor.organizer_name
    #     except Vendor.DoesNotExist:
    #         return None
    #     return None
    
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
            raise serializers.ValidationError(constants.ERROR_NOT_ENOUGH_TICKETS)
        
        if ticket_count > 5:
            raise serializers.ValidationError(constants.ERROR_MAX_TICKETS_EXCEEDED)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        ticket_type = self.context['ticket_type']
        user = self.context['request'].user

        # Calculate the ticket price based on ticket type and count
        ticket_count = validated_data['ticket_count']
        ticket_price = ticket_type.price * ticket_count

        # timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        # qr_data = f"Ticket ID: {ticket_type.id}-{user.id}-{timestamp}"

        # Create the ticket instance
        ticket = Ticket.objects.create(
            ticket_type=ticket_type,
            user=user,
            ticket_price=ticket_price,
            ticket_count=ticket_count,
            ticket_status='active'
            # qr_code=generate_qr_code(qr_data)
        )

        # Update the sold count of the ticket type
        ticket_type.sold_count += ticket_count
        ticket_type.save(update_fields=['sold_count'])

        return ticket



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
    class Meta:
        model = Ticket
        fields = '__all__'
       


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

   