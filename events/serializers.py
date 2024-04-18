from rest_framework import serializers
from .models import Event, TicketType, Venue,Ticket
from customadmin.models import Category, Location
from django.utils.translation import gettext_lazy as _


class TicketTypeSerializer(serializers.ModelSerializer):
    sold_count = serializers.ReadOnlyField()
    event = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.ReadOnlyField()

    class Meta:
        model = TicketType
        fields = ['id', 'type_name', 'ticket_image', 'price', 'count', 'sold_count', 'event']



class EventCreateSerializer(serializers.Serializer):
    venue = serializers.CharField(max_length=255, required=True)
    location = serializers.CharField(max_length=255, required=True)
    categories = serializers.ListSerializer(child=serializers.CharField())
    event_name = serializers.CharField(max_length=255)
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
            raise serializers.ValidationError(_("Venue is already booked for the specified date range"))

        # Check if an event with the same name already exists
        if Event.objects.filter(event_name=attrs['event_name']).exists():
            raise serializers.ValidationError(_("An event with the same name already exists"))

        return attrs

    def validate_categories(self, value):
        if not value:
            raise serializers.ValidationError("At least one category must be provided.")
        return value
    
    

    def create(self, validated_data):
        venue_name = validated_data.pop('venue')
        location_name = validated_data.pop('location')
        categories_data = validated_data.pop('categories')
        ticket_types_data = validated_data.pop('ticket_types')
        

        # Get or create venue
        venue, _ = Venue.objects.get_or_create(name=venue_name)

        # Get or create location
        location, _ = Location.objects.get_or_create(name=location_name)

        # Replace venue and location with venue_name and location_name respectively
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



class EventRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class EventUpdateSerializer(serializers.Serializer):
    venue = serializers.CharField(max_length=255, required=True)
    location = serializers.CharField(max_length=255, required=False)
    categories = serializers.ListSerializer(child=serializers.CharField(), required=False)
    event_name = serializers.CharField(max_length=255, required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    event_img_1 = serializers.ImageField(required=False)
    event_img_2 = serializers.ImageField(required=False, allow_null=True)
    event_img_3 = serializers.ImageField(required=False, allow_null=True)
    about = serializers.CharField(required=False)
    instruction = serializers.CharField(required=False, allow_blank=True)
    terms_and_conditions = serializers.CharField(required=False)
    ticket_types = serializers.ListSerializer(child=TicketTypeSerializer())

    def validate(self, attrs):
        Venue_name = attrs.get('venue')
        categories_data = attrs.get('categories', [])
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        location_name = attrs.get('location')

        # Check if location exists or create a new one
        if location_name:
            location, _ = Location.objects.get_or_create(name=location_name)
            attrs['location'] = location

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
                raise serializers.ValidationError(_("venue is already booked for the specified date range"))

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
        instance.save()

        # Clear existing categories and add new ones
        categories_data = validated_data.get('categories', [])
        for category_name in categories_data:
            category = Category.objects.get(name=category_name)
            instance.categories.add(category)

        return instance










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

   