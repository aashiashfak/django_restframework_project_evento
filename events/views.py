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
from .models import Event , TicketType ,Ticket, Payment, Venue, WishList
from .serializers import (
    EventSerializer,
    TicketTypeSerializer,
    TicketBookingSerializer,
    PaymentConfirmationSerializer,
    TicketSerializer,
    TrendingEventSerializer,
    WishListSerializer
)
from customadmin.serializers import LocationSerializer, VenueSerializer
from customadmin.models import Location
from .filters import EventFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied ,NotFound
from rest_framework import status
from django.http import Http404 
from django.utils import timezone
from customadmin.utilities import cached_queryset
from .utilities import initiate_razorpay_payment, verify_razorpay_signature,generate_qr_code
from rest_framework.permissions import IsAuthenticated
from accounts import constants
from customadmin.serializers import CategorySerializer
from customadmin.models import Category
from django.db.models import F
from vendors.pagination import CustomPagination





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
            return (
                Event.objects.select_related('venue','location','vendor__vendor_details__user'
                ).prefetch_related('categories','ticket_types').filter(location=location_id, status='active')
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
                return Event.objects.select_related(
                        'venue','location','vendor__vendor_details__user'
                    ).prefetch_related('categories','ticket_types').get(id=event_id)
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
    search_fields = [ 'event_name', 'venue__name', 'location__name', 'categories__name', 'organizer_name']
    pagination_class = CustomPagination
    
    def get_queryset(self):
        return cached_queryset(
            'active_events',
            lambda: Event.objects.select_related(
                'venue', 'location', 'vendor__vendor_details__user'
            ).prefetch_related(
                'categories', 'ticket_types'
            ).filter(
                status='active'
            ).annotate(
                organizer_name=F('vendor__vendor_details__organizer_name')
            ),
            timeout=60
        )


class CategoryListAPIView(generics.ListAPIView):
    """
    API view for listing categories.
    """
     
    serializer_class = CategorySerializer

    def get_queryset(self):
        return cached_queryset('categories_queryset', lambda: Category.objects.all(), timeout=500)

class VenueListApiView(generics.ListAPIView):
    """
    API view for listing categories.
    """
    serializer_class = VenueSerializer

    def get_queryset(self):
        return cached_queryset('venue_queryset', lambda: Venue.objects.all(), timeout=500)

class WishListAPIView(APIView):
    """
    API view for listing, creating, and deleting wishlist items.
    """
    permission_classes=[IsAuthenticated]
    def post(self, request, event_id, *args, **kwargs):
        """
        Adds an event to the user's wish list.
        """
        user = request.user
        data = {'user': user.id, 'event': event_id}
        serializer = WishListSerializer(data=data, context={'request': request, 'event_id': event_id})
        if serializer.is_valid():
            serializer.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, event_id):
        """
        Deletes a wishlist item by ID.
        """
        try:
            wishlist_item = WishList.objects.get(event=event_id, user=request.user)
            wishlist_item.delete()
            return Response({"message": "Wishlist item deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except WishList.DoesNotExist:
            return Response({"error": "Wishlist item not found"}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        """
        Retrieves the authenticated user's wish list items.
        """
        user = request.user

        wishlist_items =  WishList.objects.filter(user=user)

        serializer = WishListSerializer(wishlist_items, many=True)
        return Response(serializer.data)
    


class TicketTypeListAPIView(generics.ListAPIView):
    """
    API view for listing ticket types by event ID.
    """
    serializer_class = TicketTypeSerializer

    def get_queryset(self):
        event_id = self.kwargs.get('event_id')

        if event_id:
            return TicketType.objects.select_related('event').filter(event_id=event_id)
        else:
            return TicketType.objects.none()
        


class TrendingEventAPIView(APIView):
    """
    API view for fetching trending events based on booking count in the last 7 days.
    """

    def get(self, request, format=None):

        trending_events = TrendingEventSerializer.get_trending_events()
        serializer = TrendingEventSerializer(trending_events, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    


class TicketBookingAPIView(APIView):
    """
    API view for initiating ticket booking and Razorpay payment.
    """
    permission_classes=[IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print('user:',request.user)
        print('hai')
        
        if not request.user.is_active:
            return Response({"error": "Account not active"}, status=status.HTTP_403_FORBIDDEN)

        ticket_id = kwargs.get('ticket_id')
        ticket_count = request.data.get('ticket_count')

        print('ticket id is okey')

        try:
            ticket_type = TicketType.objects.get(pk=ticket_id)
        except TicketType.DoesNotExist:
            return Response({"error": "Ticket type not found"}, status=status.HTTP_404_NOT_FOUND)

        # Validate the booking
        serializer = TicketBookingSerializer(data=request.data, context={'ticket_type': ticket_type})
        serializer.is_valid(raise_exception=True)

        # Create a payment order
        payment_data = initiate_razorpay_payment(ticket_id, ticket_count)

        if 'error' in payment_data:
            # Handle the error case
            return Response({"error": payment_data['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save payment data to be confirmed later
        Payment.objects.create(
            order_id=payment_data['order_id'],
            amount=payment_data['amount'],
            status='pending',
            ticket_type=ticket_type,
            ticket_count=ticket_count
        )

        return Response(payment_data, status=status.HTTP_200_OK)

        

from django.conf import settings
import json
import hmac
import hashlib


class HandleRazorpayWebhookView(APIView):
    """
    API endpoint for handling Razorpay webhooks.
    """
    def post(self, request):
        try:
            print('Entered inside webhook post req.')

            webhook_secret_key = settings.RAZORPAY_API_SECRET
            received_data = json.loads(request.body)
            received_signature = request.headers.get('X-Razorpay-Signature')

            # Print the received signature and payload for debugging
            print('Received Signature:', received_signature)
            print('Received Payload:', request.body.decode('utf-8'))

            # Generate signature for comparison
            payload = request.body.decode('utf-8')  # Ensure payload is a string
            generated_signature = hmac.new(
                key=webhook_secret_key.encode('utf-8'),
                msg=payload.encode('utf-8'),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            print('Generated Signature:', generated_signature)

            if not verify_razorpay_signature(received_signature, payload, webhook_secret_key):
                print('Signature mismatch. Response tampered.')
                return Response({"error": "Invalid webhook signature"}, status=status.HTTP_400_BAD_REQUEST)

            # Process the valid webhook
            order_id = received_data.get('payload', {}).get('order', {}).get('id')
            payment_status = received_data.get('payload', {}).get('payment', {}).get('status')

            try:
                payment = Payment.objects.get(order_id=order_id)
            except Payment.DoesNotExist:
                return Response({"error": "Payment not found for this order ID"}, status=status.HTTP_404_NOT_FOUND)

            if payment_status == 'captured':
                # Payment is successful, create the ticket
                ticket = Ticket.objects.create(
                    user=payment.user,  # Use the user from the payment
                    ticket_type=payment.ticket_type,
                    ticket_count=payment.ticket_count,
                    ticket_price=payment.amount,
                    booking_time=timezone.now(),
                    ticket_status='confirmed',
                    qr_code=generate_qr_code(payment)  # Generate a QR code and save it to the ticket
                )

                print('Ticket created successfully')

                # Update payment status
                payment.status = 'captured'
                payment.save()

                # Update the sold count of the ticket type
                payment.ticket_type.sold_count += payment.ticket_count
                payment.ticket_type.save(update_fields=['sold_count'])

                print('Payment completed')

                return Response({"message": "Payment successful and ticket booked"}, status=status.HTTP_200_OK)
            else:
                payment.status = payment_status
                payment.save()
                return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Error verifying Razorpay signature: {e}")
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class ConfirmTicketAPIView(APIView):
    """
    API view to confirm ticket booking after successful payment.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print('entered in conform ticket')
        order_id = request.data.get('order_id')
        payment_id = request.data.get('payment_id')
        ticket_id = request.data.get('ticket_id')
        ticket_count = request.data.get('ticket_count')

        try:
            ticket_type = TicketType.objects.get(pk=ticket_id)
            payment = Payment.objects.get(order_id=order_id)

            if payment.status == 'pending':
                # Mark payment as captured
                payment.status = 'captured'
                payment.save()

                print('paymentsaved')

                ticket_price = payment.amount / 100

                # Create the ticket
                ticket = Ticket.objects.create(
                    user=request.user,
                    ticket_type=ticket_type,
                    ticket_count=ticket_count,
                    ticket_price=ticket_price,
                    ticket_status='active',
                    qr_code=generate_qr_code(payment)
                )

                # Update the sold count of the ticket type
                ticket_type.sold_count += ticket_count
                ticket_type.save(update_fields=['sold_count'])

                return Response({"message": "Ticket booked successfully"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "Payment already processed or invalid"}, status=status.HTTP_400_BAD_REQUEST)

        except (TicketType.DoesNotExist, Payment.DoesNotExist) as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({"error": "Internal Server Error:",}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response({"error": constants.ERROR_TICKET_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        if request.user != ticket.user:
            return Response({"error": constants.NO_PERMISSION_CANCEL}, status=status.HTTP_403_FORBIDDEN)

        if ticket.ticket_status == 'canceled':
            return Response({"message": constants.MESSAGE_TICKET_ALREADY_CANCELED}, status=status.HTTP_400_BAD_REQUEST)
        
         # Check if the cancellation is within two minutes of booking
        time_elapsed = timezone.now() - ticket.booking_date
        if time_elapsed.total_seconds() > 120:  
            return Response({"error": constants.ERROR_CANNOT_CANCEL_AFTER_TWO_MINUTES}, status=status.HTTP_400_BAD_REQUEST)

        ticket.ticket_status = 'canceled'
        ticket.save(update_fields=['ticket_status'])

        ticket_type = ticket.ticket_type
        ticket_type.sold_count -= ticket.ticket_count
        ticket_type.save(update_fields=['sold_count'])

        serializer = TicketSerializer(ticket)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


# class HandleRazorpayWebhookView(APIView):
#     """
#     API endpoint for handling Razorpay webhooks.
#     """
#     def post(self, request):
#         # Retrieve data from Razorpay webhook request
#         data = request.data

#         # Extract signature and payload from webhook data
#         signature = request.headers.get('X-Razorpay-Signature')

#         print(f"signature value {signature}")

#         payload = json.dumps(data)

#         # Verify the signature
#         is_valid_signature = verify_razorpay_signature(signature, payload)

#         if not is_valid_signature:
#             return Response({"error": "Invalid webhook signature"}, status=status.HTTP_400_BAD_REQUEST)

#         # Extract order ID and payment ID from webhook data
#         order_id = data.get('payload', {}).get('order', {}).get('id')
#         payment_id = data.get('payload', {}).get('payment', {}).get('id')

#         try:
#             payment = Payment.objects.get(order_id=order_id)
#         except Payment.DoesNotExist:
#             return Response({"error": "Payment not found for this order ID"}, status=status.HTTP_404_NOT_FOUND)

#         # Update payment status based on Razorpay webhook data (e.g., 'captured' for successful payment)
#         payment.status = data.get('payload', {}).get('payment', {}).get('status')
#         payment.save(update_fields=['status'])

#         return Response({"message": "Payment status updated successfully"}, status=status.HTTP_200_OK)
    

