# from rest_framework import status
# from rest_framework.response import Response

from .serializers import (
    VendorSignupSerializer,
    VendorSerializer,
    VendorLoginSerializer,
    EmailSerializer,
    ChangeForgetPasswordSerializer,
    VendorProfileSerializer,
)
# from rest_framework.views import APIView
# from django.utils import timezone
# from datetime import timedelta
from accounts.serializers import OTPVerificationSerializer
# from accounts.models import PendingUser
from django.conf import settings
from accounts.utilities import generate_otp
from .utilities import send_otp_email
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from accounts import constants
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from accounts.models import CustomUser,PendingUser,VendorManager,Follow
from accounts.permissions import IsVendor, IsActiveUser




from rest_framework import status,generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import VendorSignupSerializer
from django.utils import timezone
from datetime import timedelta


class VendorSignupView(APIView):
    """
    View for vendor signup.
    This view handles the signup process for vendors. It sends an OTP to the 
    provided email address for verification before creating the vendor account.
    """
    def post(self, request):
        """
        Handle POST request for vendor signup.
        This method validates the provided data, sends an OTP to the provided 
        email address, and stores the vendor signup data in the session.
        Return Response object containing the result of the signup operation.
        """
        serializer = VendorSignupSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            # Save data in session
            request.session['vendor_signup_data'] = serializer.validated_data

            # Get email from validated data
            email = serializer.validated_data['email']

            otp = generate_otp()
            print('generated otp',otp)
            expiry_time = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
            pending_user, created = PendingUser.objects.update_or_create(
                email=email,
                defaults={'otp': otp, 'expiry_time': expiry_time}
            )

            try:
                send_otp_email(email, serializer.validated_data['contact_name'], otp)
                return Response({'message': constants.OTP_SENT_SUCCESSFULLY}, status=status.HTTP_200_OK)
            except Exception as e:
                pending_user.delete()
                return Response({'error': constants.FAILED_TO_SEND_OTP_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VendorVerifyOtpView(APIView):
    """
    View for verifying OTP during vendor signup.
    """
    def post(self, request):
        """
        Handle POST request for OTP verification.
        """
        otp_serializer = OTPVerificationSerializer(data=request.data)
        if otp_serializer.is_valid():
            otp = otp_serializer.validated_data['otp']
            vendor_data = request.data.get('vendorData', None)

            print(vendor_data)
            
            if vendor_data is None:
                return Response(
                    {'error': 'Vendor data is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            email = vendor_data.get('email')

            # Print extracted values for debugging
            print('Received OTP:', otp)
            print('Vendor Data:', vendor_data)
            print('Email:', email)

            try:
                pending_user = PendingUser.objects.get(email=email, otp=otp)
                if pending_user.expiry_time < timezone.now():
                    pending_user.delete()
                    return Response(
                        {'error': constants.OTP_EXPIRED_ERROR},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                vendor_data.pop('confirm_password', None)
                password = vendor_data.pop('password', None)

                # Create vendor user and vendor using custom manager
                vendor_manager = VendorManager()
                user, vendor = vendor_manager.create_vendor_user(vendor_data, password)

                access_token = RefreshToken.for_user(user)
                refresh_token = RefreshToken.for_user(user)

                pending_user.delete()

                vendor_serializer = VendorSerializer(vendor)
                return Response({
                    'vendor': vendor_serializer.data,
                    'access_token': str(access_token),
                    'refresh_token': str(refresh_token),
                }, status=status.HTTP_200_OK)
            except PendingUser.DoesNotExist:
                print('invalid otp')
                return Response(
                    {'error': constants.INVALID_OTP},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Print serializer errors for debugging
            print('OTP serializer errors:', otp_serializer.errors)
            return Response(otp_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class VendorLoginView(APIView):
    """
    View for vendor login.
    This view handles the authentication of vendor login requests.
    """

    def post(self, request):
        """
        Handle POST request for vendor login.
        This method validates the provided credentials and generates access tokens
        for authenticated vendors.
        """
        serializer = VendorLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VendorForgetPasswordOTPsent(APIView):
    """
    View for sending OTP during forget password process.
    """
    def post(self, request):
        """
        Handle POST request for sending OTP.
        This method sends an OTP to the email address of the vendor who wants to
        reset their password.
        """
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            contact_name = email.split('@')[0]  
            otp = generate_otp()

            try:
                vendor = CustomUser.objects.get(email=email)
                if not vendor.is_vendor:
                    return Response(
                        {"error": constants.ERROR_VENDOR_EMAIL_NOT_FOUND},
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
                expiry_time = timezone.now() + timedelta(
                    minutes=settings.OTP_EXPIRY_MINUTES
                )
                pending_user, created = PendingUser.objects.update_or_create(
                    email=email,
                    defaults={'otp': otp, 'expiry_time': expiry_time}
                )

                try:
                    send_otp_email(email, contact_name, otp)
                    return Response(
                        {"detail": constants.OTP_SENT_SUCCESSFULLY},
                        status=status.HTTP_200_OK
                    )
                except Exception:
                    pending_user.delete()
                    return Response(
                        {"error": constants.FAILED_TO_SEND_OTP_ERROR},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except CustomUser.DoesNotExist:
                return Response(
                    {"error": constants.ERROR_VENDOR_EMAIL_NOT_FOUND},
                    status=status.HTTP_404_NOT_FOUND
                    )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyOTPView(APIView):
    """
    View for verifying OTP.
    This view handles the verification of OTP sent during various processes,
    such as password reset.
    """
    def post(self, request):
        """
        Handle POST request for OTP verification.
        This method validates the OTP provided by the user 
        Return Response object containing the result of the OTP verification process.
        """
        serializer = OTPVerificationSerializer(data=request.data) 
        if serializer.is_valid():
            otp = request.data.get('otp')
            try:
                email = request.session['email']
            except Exception:
                return Response(
                    {"error": constants.EMAIL_NOT_FOUND_ERROR},
                    status=status.HTTP_404_NOT_FOUND
                )
            try:
                pending_user = PendingUser.objects.get(email=email, otp=otp)
                if pending_user.expiry_time < timezone.now():
                    pending_user.delete()
                    return Response(
                        {'error': constants.OTP_EXPIRED_ERROR},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    pending_user.delete()
                    return Response(
                        {'detail': constants.OTP_VERIFIED_SUCCESSFULLY},
                        status=status.HTTP_200_OK
                    )
            except PendingUser.DoesNotExist:
                return Response(
                    {'error': constants.INVALID_OTP},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class ChangePasswordView(APIView):
    """
    View for changing vendor password.
    """
    def post(self, request):
        """
        Handle POST request for changing password.
        This method validates the provided data and changes the password of the vendor.
        Return Response object containing the result of the password change process.
        """
        serializer = ChangeForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            new_password = serializer.validated_data.get('password')
            hashed_password = make_password(new_password)
            email = request.session.get('email')
            if email:
                try:
                    vendor = CustomUser.objects.get(email=email)
                    vendor.password = hashed_password
                    vendor.save(update_fields=['password'])
                    return Response(
                        {"detail": constants.PASSWORD_CHANGED_SUCCESSFULLY},
                        status=status.HTTP_200_OK
                        )
                except CustomUser.DoesNotExist:
                    return Response(
                        {"error": constants.ERROR_VENDOR_EMAIL_NOT_FOUND},
                        status=status.HTTP_404_NOT_FOUND
                        )
            else:
                return Response(
                    {"error": constants.EMAIL_NOT_FOUND_ERROR},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


from django.shortcuts import get_object_or_404        
from events.models import Event,TicketType,Ticket
from events.serializers import (
    EventCreateSerializer,
    EventSerializer,
    EventUpdateSerializer,
    TicketTypeSerializer,
    UserTicketDetailsSerializer,
    TicketTypeCreateSerializer

)
from django.db.models import Sum
from customadmin.utilities import cached_queryset
from django.core.cache import cache
from django.db.models import Count
from .pagination import CustomPagination
from rest_framework.filters import SearchFilter

 

class VendorProfileAPIView(APIView):
    """
    View for retrieving and updating vendor profile information.
    """
    permission_classes = [IsAuthenticated, IsVendor]
    
    def get(self, request):
        """
        Retrieve the profile information of the authenticated vendor.
        """
        vendor = getattr(request.user, 'vendor_details', None)
        print(vendor)
        
        if not vendor:
            return Response({'error': constants.ERROR_VENDOR_PROFILE_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the Vendor data using VendorSerializer
        serializer = VendorSerializer(vendor)
        return Response(serializer.data)

    def put(self, request):
        """
        Update the profile information of the authenticated vendor.
        """
        vendor = getattr(request.user, 'vendor_details', None)
        print(vendor)
        
        if not vendor:
            return Response({'error': constants.ERROR_VENDOR_PROFILE_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        serializer = VendorProfileSerializer(vendor, data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

from rest_framework.parsers import MultiPartParser




class CreateEventView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsVendor, IsActiveUser]
    parser_classes = [MultiPartParser]

   

    def get(self, request):
        vendor = request.user
        events = cached_queryset(
            f'vendor_event_listing${vendor.id}',
            lambda: Event.objects.select_related('venue', 'location').prefetch_related('categories', 'ticket_types', 'vendor').filter(vendor=vendor),
            timeout=60
        )
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

    def post(self, request):
        vendor = request.user
        print(request.data)
        data = request.data.dict()

        # Process categories as a list
        data['categories'] = request.data.getlist('categories[]')

        # Process ticket types - This section is refactored to correctly handle ticket types
        ticket_types = []
        i = 0
        while f'ticket_types[{i}][type_name]' in data:
            ticket_type = {
                'type_name': request.data.get(f'ticket_types[{i}][type_name]'),
                'price': request.data.get(f'ticket_types[{i}][price]'),
                'count': request.data.get(f'ticket_types[{i}][count]'),
                'sold_count': request.data.get(f'ticket_types[{i}][sold_count]'),
                'ticket_image': request.data.get(f'ticket_types[{i}][ticket_image]'),
            }
            ticket_types.append(ticket_type)
            i += 1
        data['ticket_types'] = ticket_types

        processed_data = data
        print('processed_data',processed_data)
        # Now pass the processed data to the serializer
        serializer = EventSerializer(data=data)
        if serializer.is_valid():
            # Set the vendor before saving the event - Change made here
            serializer.validated_data['vendor'] = request.user  
            event = serializer.save()  # Save returns the instance now
            cache.delete(f'vendor_event_listing${vendor.id}')
            print('expecting error here')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


        

class VendorEventDetailView(APIView):
    """
    API view for retrieving, updating, and deleting specific events 
    associated with the authenticated vendor.
    """
    permission_classes = [IsAuthenticated, IsVendor]
    parser_classes = [MultiPartParser]   

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id, vendor=request.user)
        serializer = EventSerializer(event)
        return Response(serializer.data)

    def put(self, request, event_id):
        # Fetch the event or raise a 404 error if not found
        vendor = request.user
        event = get_object_or_404(Event, pk=event_id, vendor=request.user)
        

        # Handle the categories and ticket types data
        data = request.data.dict()
        
        # Print the raw request data
        print("Raw request data:", request.data)

        # Process categories
        categories_data = request.data.getlist('categories[]')
        if categories_data:
            data['categories'] = categories_data
        else:
            # Remove categories from data if not provided
            data.pop('categories', None)

        # Conditionally process ticket types only if they are present in the request
        if any(f'ticket_types[{i}][type_name]' in request.data for i in range(len(request.data))):
            ticket_types = []
            i = 0
            
            while f'ticket_types[{i}][type_name]' in request.data:
                ticket_type = {
                    'type_name': request.data.get(f'ticket_types[{i}][type_name]'),
                    'price': request.data.get(f'ticket_types[{i}][price]'),
                    'count': request.data.get(f'ticket_types[{i}][count]'),
                    'sold_count': request.data.get(f'ticket_types[{i}][sold_count]'),
                    'ticket_image': request.data.get(f'ticket_types[{i}][ticket_image]'),
                }
                ticket_types.append(ticket_type)
                i += 1
            
            data['ticket_types'] = ticket_types
            print(f"Processed ticket types: {ticket_types}")
        else:
            # Remove ticket_types from data if not provided
            data.pop('ticket_types', None)

        # Create and validate the serializer
        serializer = EventSerializer(instance=event, data=data, partial=True)
        print(f"Serializer data: {data}")
        
        if serializer.is_valid():
            print("Serializer is valid.")
            serializer.save()
            cache.delete(f'vendor_event_listing${vendor.id}')
            return Response(serializer.data)
        else:
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, event_id):
        vendor = request.user
        event = get_object_or_404(Event, pk=event_id, vendor=request.user)
        event.delete()
        cache.delete(f'vendor_event_listing${vendor.id}')
        return Response({"message": f"Event {event.event_name} deleted succussfully"},status=status.HTTP_204_NO_CONTENT)
    

class TicketTypeListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating ticket types for a specific event 
    associated with the authenticated vendor.
    """
    serializer_class = TicketTypeCreateSerializer
    permission_classes = [IsAuthenticated, IsVendor]

    def get_queryset(self):
        event_id = self.kwargs.get('event_id')
        vendor = self.request.user
        event = get_object_or_404(Event, id=event_id, vendor=vendor)
        return TicketType.objects.filter(event=event)

    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_id')
        vendor = self.request.user
        event = get_object_or_404(Event, id=event_id, vendor=vendor)
        cache.delete(f'vendor_event_listing${vendor.id}')
        serializer.save(event=event)

class TicketTypeRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a TicketType
    associated with a specific event of the authenticated vendor.
    """
    
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = TicketTypeCreateSerializer
    lookup_field = 'id'

    def get_queryset(self):
        event_id = self.kwargs.get('event_id')
        vendor = self.request.user

        # Ensure the event belongs to the vendor
        event = get_object_or_404(Event, id=event_id, vendor=vendor)

        # Filter ticket types for the specific event
        return TicketType.objects.filter(event=event)

    def get(self, request, event_id=None, id=None):
        return self.retrieve(request, id)

    def put(self, request, event_id=None, id=None):
        vendor = request.user
        cache.delete(f'vendor_event_listing${vendor.id}')
        return self.update(request, id)
    
    def patch(self, request, event_id=None, id=None):
        print(request.data)
        vendor = request.user
        cache.delete(f'vendor_event_listing${vendor.id}')
        return self.partial_update(request, id)

    def delete(self, request, event_id=None, id=None):
        vendor = request.user
        cache.delete(f'vendor_event_listing${vendor.id}')
        return self.destroy(request, id)

class VendorDashboardAPIView(APIView):
    """
    API view for the vendor dashboard.
    Provides statistics about the vendor's events and tickets.
    """
    permission_classes = [IsAuthenticated, IsVendor]

    def get(self, request):
        vendor = request.user

        cache_key = f'vendor_dashboard_data_{vendor.id}'
        
        data = cache.get(cache_key)
        if data is not None:
            print('Fetched from cache')

        if data is None:
            print('Fetched from DB')

            total_events_count = Event.objects.filter(vendor=vendor).count()

            completed_events_count = Event.objects.filter(vendor=vendor, status='completed').count()

            active_events_count = Event.objects.filter(vendor=vendor, status='active').count()
            disabled_events_count = Event.objects.filter(vendor=vendor, status='disabled').count()

            total_tickets_count = TicketType.objects.filter(
                event__vendor=vendor).aggregate(total_tickets_count=Sum('count'))['total_tickets_count']
            total_tickets_count = total_tickets_count if total_tickets_count is not None else 0
            
            booked_tickets_count = TicketType.objects.filter(
                event__vendor=vendor).aggregate(booked_tickets_count=Sum('sold_count'))['booked_tickets_count']
            booked_tickets_count = booked_tickets_count if booked_tickets_count is not None else 0
            
            top_users = (
                Ticket.objects.filter(ticket_type__event__vendor=vendor)
                .exclude(ticket_status='canceled')
                .values('user__username', 'user__email', 'user__phone_number')
                .annotate(total_tickets=Sum('ticket_count'))
                .order_by('-total_tickets')
                .values('user__username', 'user__email', 'user__phone_number', 'total_tickets')
            )[:10]
           
            total_earnings = Ticket.objects.filter(
                ticket_type__event__vendor=vendor
            ).exclude(
                ticket_status='canceled'
            ).aggregate(total_earnings=Sum('ticket_price'))['total_earnings']
            total_earnings = total_earnings if total_earnings is not None else 0

            total_followers = Follow.objects.filter(vendor__user=vendor).count()

            print('Total followers:', total_followers)

            # Construct data dictionary
            data = {
                'total_events_count': total_events_count,
                'completed_events_count': completed_events_count,
                'disabled_events_count': disabled_events_count,
                'active_events_count': active_events_count,
                'total_tickets_count': total_tickets_count,
                'booked_tickets_count': booked_tickets_count,
                'total_earnings': total_earnings,
                'total_followers': total_followers,
                'top_users': top_users,
            }

            # Store data in cache
            cache.set(cache_key, data, timeout=3600)

        return Response(data)
    
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter
from events.models import Ticket


# -------------------------------------------- Booked Users Api ------------------------------------------------------------------

class VendorBookedTicketsAPIView(ListAPIView):
    """
    API view to get all users who booked a vendor's events along with their ticket details and event names.
    """
    serializer_class = UserTicketDetailsSerializer
    pagination_class = CustomPagination
    permission_classes = [IsVendor]
    filter_backends = [SearchFilter]
    search_fields = ['user__username', 'ticket_type__event__event_name', 'ticket_type__type_name']

    def get_queryset(self):
        return Ticket.objects.select_related(
            'ticket_type', 'user', 'ticket_type__event'
        ).filter(ticket_type__event__vendor=self.request.user)

from django.db.models.functions import TruncDate

class VendorTicketBookingDataView(APIView):
    """
    API endpoint to retrieve ticket count data for a vendor for the last 7 days.
    """
    permission_classes = [IsVendor] 

    def get(self, request, date):
        vendor = request.user  # Assuming the user is the vendor
        try:
            end_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=400)

        # Make the dates timezone-aware and set start and end times
        end_date = timezone.make_aware(timezone.datetime.combine(end_date, timezone.datetime.max.time()))
        start_date = timezone.make_aware(timezone.datetime.combine(end_date - timezone.timedelta(days=6), timezone.datetime.min.time()))

        # Filter tickets by vendor and date range, then aggregate by day
        bookings = (
            Ticket.objects.filter(
                booking_date__range=[start_date, end_date],
                ticket_type__event__vendor=vendor  # Filter by vendor
            )
            .exclude(ticket_status='canceled')  
            .annotate(date=TruncDate('booking_date'))
            .values('date')
            .annotate(total_bookings=Sum('ticket_count'))  # Sum the ticket_count
            .order_by('date')
        )

        # Convert bookings queryset to a dictionary for quick lookup
        booking_dict = {booking['date']: booking['total_bookings'] for booking in bookings}

        # Generate the date range list
        booking_data = []
        for i in range(7):
            current_date = (start_date + timezone.timedelta(days=i)).date()
            date_str = current_date.strftime('%Y-%m-%d')
            total_bookings = booking_dict.get(current_date, 0)
            booking_data.append({
                'date': date_str,
                'total_bookings': total_bookings
            })

        return Response(booking_data)
    

from django.utils import timezone
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models.functions import TruncDate

class VendorReportGeneratorView(APIView):
    """
    API endpoint to retrieve ticket count data for a vendor for the last 7 days.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        vendor = request.user
        print("Vendor:", vendor)

        try:
            end_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
            print("Parsed date:", end_date)
        except ValueError:
            print("Invalid date format")
            return Response({'error': 'Invalid date format'}, status=400)

        # Set the date range for the report (last 7 days)
        end_date = timezone.make_aware(timezone.datetime.combine(end_date, timezone.datetime.max.time()))
        start_date = timezone.make_aware(timezone.datetime.combine(end_date - timezone.timedelta(days=6), timezone.datetime.min.time()))
        print("Date range:", start_date, "to", end_date)

        # Generate a list of all dates in the range
        date_range = [start_date + timezone.timedelta(days=i) for i in range(7)]
        date_range_str = [single_date.date().strftime('%Y-%m-%d') for single_date in date_range]

        # Filter and aggregate ticket bookings
        try:
            bookings = (
                Ticket.objects.filter(
                    booking_date__range=[start_date, end_date],
                    ticket_type__event__vendor=vendor
                )
                .values(
                    'id',  # Ensure each ticket is unique
                    'booking_date',
                    'ticket_type__event__event_name',
                    'ticket_status',
                    'ticket_price',
                    'ticket_type__type_name',
                    'user__username',
                    'user__email',
                    'user__phone_number',
                    'ticket_count',
                )
                .order_by('booking_date')
            )
        except Exception as e:
            print("Error querying ticket bookings:", e)
            return Response({'error': 'Failed to query ticket bookings'}, status=500)

        # Initialize totals and daily bookings
        total_tickets = 0
        total_amount = 0
        daily_bookings = {}

        # Process bookings to calculate totals and group by date
        for booking in bookings:
            booking_date = booking['booking_date'].strftime('%Y-%m-%d')
                
            # Initialize daily bookings for the date
            if booking_date not in daily_bookings:
                daily_bookings[booking_date] = []
                
                # Add booking to the specific date
            daily_bookings[booking_date].append({
                "date": booking_date,
                "event_name": booking['ticket_type__event__event_name'],
                "username": booking['user__username'],
                "email": booking['user__email'],
                "phone_number": booking['user__phone_number'],
                "ticket_count": booking['ticket_count'],
                "ticket_price": booking['ticket_price'],
                "ticket_status": booking['ticket_status'],
                "ticket_type": booking['ticket_type__type_name'],
            })

            # Update totals
            total_tickets += booking['ticket_count']
            if booking['ticket_status'] != 'canceled':  # Only add active ticket prices
                total_amount += booking['ticket_price']

            # Prepare the response
        response_data = {
            "start_date": start_date.strftime('%d %b %Y'),
            "end_date": end_date.strftime('%d %b %Y'),
            "total_tickets": total_tickets,
            "total_amount": total_amount,
            "daily_bookings": daily_bookings,
        }

        return Response(response_data)
    
