# from django.shortcuts import render

# # Create your views here.
# from rest_framework import viewsets
# from .models import Event
# from rest_framework import viewsets
# from rest_framework.response import Response
# from .models import Event
# from .serializers import EventCreateSerializer
# from accounts.permissions import IsVendor
# from rest_framework.permissions import IsAuthenticated

# class VendorEventViewSet(viewsets.ModelViewSet):
#     queryset = Event.objects.all()  # This is just a placeholder, will be overridden by get_queryset
#     serializer_class = EventCreateSerializer
#     permission_classes = [IsAuthenticated, IsVendor]

#     def perform_create(self, serializer):
#         serializer.save(vendor=self.request.user)  # Assign the current user as the vendor

#     def perform_update(self, serializer):
#         serializer.save(vendor=self.request.user)  # Ensure the current user is the vendor

#     def get_queryset(self):
#         return Event.objects.filter(vendor=self.request.user)


from rest_framework import generics
from rest_framework import filters
from .models import Event , TicketType
from .serializers import (
    EventSerializer,
    TicketTypeSerializer
)
from customadmin.serializers import LocationSerializer
from customadmin.models import Location
from .filters import EventFilter
from django_filters.rest_framework import DjangoFilterBackend




class LocationListAPIView(generics.ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class EventByLocationAPIView(generics.ListAPIView):
    serializer_class = EventSerializer

    def get_queryset(self):
        location_id = self.request.query_params.get('location_id')

        if location_id:
            return Event.objects.filter(location=location_id)
        else:
            return Event.objects.none() 
        

class EventDetailAPIView(generics.RetrieveAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class EventListAPIView(generics.ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filterset_class = EventFilter
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    search_fields = ['event_name', 'venue__name', 'location__name', 'categories__name']



class TicketTypeListAPIView(generics.ListAPIView):
    serializer_class = TicketTypeSerializer

    def get_queryset(self):
        event_id = self.kwargs.get('event_id')

        if event_id:
            return TicketType.objects.select_related('event').filter(event_id=event_id)
        else:
            return TicketType.objects.none()