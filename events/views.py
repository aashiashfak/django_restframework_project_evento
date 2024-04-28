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



import json
from rest_framework import generics
from rest_framework import filters
from .models import Event , TicketType ,Ticket,Payment
from .serializers import (
    EventSerializer,
    TicketTypeSerializer,
    TicketBookingSerializer,
    PaymentConfirmationSerializer,
    TicketSerializer,
    TrendingEventSerializer
)
from customadmin.serializers import LocationSerializer
from customadmin.models import Location
from .filters import EventFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from django.http import Http404 
from django.utils import timezone
from customadmin.utilities import cached_queryset
from .utilities import initiate_razorpay_payment, verify_razorpay_signature
import razorpay
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q




class LocationListAPIView(generics.ListAPIView):
    """
    API view for listing all locations.
    """
    serializer_class = LocationSerializer

    def get_queryset(self):
        return cached_queryset('location_queryset', lambda: Location.objects.all(),timeout=60)


class EventByLocationAPIView(generics.ListAPIView):
    """
    API view for listing events by location ID.
    """
    serializer_class = EventSerializer

    def get_queryset(self):
        location_id =  self.kwargs.get('location_id')

        if location_id:
            # return Event.objects.filter(location=location_id)
            return cached_queryset(
                'events_by_location',
                lambda: Event.objects.prefetch_related('venue','location','vendor','categories','ticket_types').filter(location=location_id),
                timeout=60
            )
        else:
            return Event.objects.none() 
        
class EventDetailAPIView(generics.RetrieveAPIView):
    """
    API view for retrieving details of a specific event.
    """
    serializer_class = EventSerializer

    def get_queryset(self):
        event_id = self.kwargs.get('pk')
        if event_id:
            try:
                return cached_queryset(
                    'event_detail',
                    lambda: Event.objects.prefetch_related('venue','location','vendor','categories','ticket_types').get(id=event_id),
                    timeout=60
                )
            except Event.DoesNotExist:
                return None
        else:
            return None

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset is None:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)
    
    


class EventListAPIView(generics.ListAPIView):
    """
    API view for listing events.
    Supports filtering by event name, venue name, location name, and category name.
    """
    
    # queryset = Event.objects.filter(status='active')
    serializer_class = EventSerializer
    filterset_class = EventFilter
    filter_backends = [filters.SearchFilter,DjangoFilterBackend]
    search_fields = ['event_name', 'venue__name', 'location__name', 'categories__name']
    
    def get_queryset(self):
        return cached_queryset(
            'active_events',
            lambda: Event.objects.prefetch_related('venue','location','vendor','categories','ticket_types',).filter(status='active'),
            timeout=60
        )


class TicketTypeListAPIView(generics.ListAPIView):
    """
    API view for listing ticket types by event ID.
    """
    serializer_class = TicketTypeSerializer

    def get_queryset(self):
        event_id = self.kwargs.get('event_id')

        if event_id:
            return cached_queryset(
                'tickets_of_event',
                lambda: TicketType.objects.select_related('event').filter(event_id=event_id),
                timeout=60
            )
        else:
            return TicketType.objects.none()
        

class TicketBookingAPIView(APIView):
    """
    API view for booking tickets.
    """

    
    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            raise PermissionDenied("You need to be logged in to book tickets.")
        
        if not request.user.is_active:
            raise PermissionDenied("Your account is not active.")

        ticket_id = kwargs.get('ticket_id')  

        try:
            ticket_type = TicketType.objects.get(pk=ticket_id)
        except TicketType.DoesNotExist:
             raise Http404("Ticket type not found.")

        serializer = TicketBookingSerializer(data=request.data, context={'ticket_type': ticket_type, 'request': request})

        if serializer.is_valid():
            serializer.save()

            return Response({"message": "Ticket booked successfully."}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


class ConfirmPaymentAPIView(APIView):
    """
    API view for confirming payment details and initiating payment.
    """

    def get(self, request, ticket_id):

        try:
            ticket = Ticket.objects.get(pk=ticket_id)
        except Ticket.DoesNotExist:
            return Response({"error": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PaymentConfirmationSerializer(ticket)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, ticket_id):
        
        if not request.user.is_authenticated:
            return Response({"error": "You need to be logged in to confirm payment."}, status=status.HTTP_401_UNAUTHORIZED)
  
        try:
            ticket = Ticket.objects.get(pk=ticket_id)
        except Ticket.DoesNotExist:
            return Response({"error": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Pass ticket_id to this function to initiate payment for the specific ticket
        payment_data = initiate_razorpay_payment(ticket_id)

        if payment_data:
            return Response({"payment_data": payment_data, "message": "Redirecting to payment initiation."}, status=status.HTTP_200_OK)
        else:
            return Response({"error":"Error during payment initiation"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   


class CancelTicketAPIView(APIView):
    """
    API view for canceling a ticket.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        ticket_id = kwargs.get('ticket_id')

        try:
            ticket = Ticket.objects.get(pk=ticket_id)
            print(ticket_id)
        except Ticket.DoesNotExist:
            return Response({"error": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user != ticket.user:
            return Response({"error": "You don't have permission to cancel this ticket."}, status=status.HTTP_403_FORBIDDEN)

        if ticket.ticket_status == 'canceled':
            return Response({"message": "Ticket is already canceled."}, status=status.HTTP_400_BAD_REQUEST)

        ticket.ticket_status = 'canceled'
        ticket.save(update_fields=['ticket_status'])

        ticket_type = ticket.ticket_type
        ticket_type.sold_count -= ticket.ticket_count
        ticket_type.save(update_fields=['sold_count'])

        serializer = TicketSerializer(ticket)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class HandleRazorpayWebhookView(APIView):
    """
    API endpoint for handling Razorpay webhooks.
    """

    def post(self, request):
        # Retrieve data from Razorpay webhook request
        data = request.data

        # Extract signature and payload from webhook data
        signature = request.headers.get('X-Razorpay-Signature')

        print(f"signature value {signature}")

        payload = json.dumps(data)

        # Verify the signature
        is_valid_signature = verify_razorpay_signature(signature, payload)

        if not is_valid_signature:
            return Response({"error": "Invalid webhook signature"}, status=status.HTTP_400_BAD_REQUEST)

        # Extract order ID and payment ID from webhook data
        order_id = data.get('payload', {}).get('order', {}).get('id')
        payment_id = data.get('payload', {}).get('payment', {}).get('id')

        try:
            payment = Payment.objects.get(order_id=order_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found for this order ID"}, status=status.HTTP_404_NOT_FOUND)

        # Update payment status based on Razorpay webhook data (e.g., 'captured' for successful payment)
        payment.status = data.get('payload', {}).get('payment', {}).get('status')
        payment.save(update_fields=['status'])

        return Response({"message": "Payment status updated successfully"}, status=status.HTTP_200_OK)
    



class TrendingEventAPIView(APIView):
    """
    API view for fetching trending events based on booking count in the last 7 days.
    """

    def get(self, request, format=None):

        trending_events = TrendingEventSerializer.get_trending_events()
        serializer = TrendingEventSerializer(trending_events, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)