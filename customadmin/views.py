from .serializers import (
    SuperuserLoginSerializer,
    CategorySerializer,
    LocationSerializer,
    VendorSerializer,
    UserSerializer,
    BannerSerializer
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import generics, mixins
from .models import Category,Location,Banner
from accounts.permissions import IsSuperuser
from rest_framework.permissions import IsAuthenticated
from .utilities import cached_queryset

from events.serializers import EventSerializer
from events.models import Event
from accounts.models import CustomUser,Vendor
from accounts import constants
from django.core.cache import cache

class SuperUserLoginView(APIView):
    """
    View for superuser login.
    This view allows superusers to authenticate and obtain JWT tokens
    for authorization.
    A list containing the permission classes applied to this view. 
    Handles POST requests for superuser login. It validates the provided credentials
    using the SuperuserLoginSerializer.
    """
    def post(self, request):
        """
        Handle POST requests for superuser login.
        This method validates the provided credentials using the SuperuserLoginSerializer.
        """
        serializer = SuperuserLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



        
        
class CategoryListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating categories.
    Only superusers are allowed to access this view.
    """

    permission_classes=[IsSuperuser,IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        return cached_queryset('categories_queryset', lambda: Category.objects.all(),timeout=500)
    
    def get(self, request):
        return self.list(request)

    def post(self, request):
        cache.delete('categories_queryset')
        return self.create(request)
    
class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a category.
    Only superusers are allowed to access this view.
    """

    permission_classes=[IsSuperuser,IsAuthenticated]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    lookup_field = 'id'

    def get(self, request, id=None):
        return self.retrieve(request, id)
    

    def put(self, request, id=None):
        cache.delete('categories_queryset')
        return self.update(request, id)
    
    def patch(self, request, id=None):
        cache.delete('categories_queryset')
        return self.partial_update(request, id)

    def delete(self, request, id=None):
        cache.delete('categories_queryset')
        return self.destroy(request, id)


class LocationListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating locations.
    Only superusers are allowed to access this view.
    """

    permission_classes=[IsSuperuser,IsAuthenticated]
    serializer_class = LocationSerializer

    def get_queryset(self):
        return cached_queryset('Location_queryset', lambda: Location.objects.all(),timeout=3600)

    def get(self, request):
        return self.list(request)

    def post(self, request):
        cache.delete('Location_queryset')
        return self.create(request)
    
class LocationRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a location.
    Only superusers are allowed to access this view.
    """

    permission_classes=[IsSuperuser,IsAuthenticated]
    serializer_class = LocationSerializer
    queryset = Location.objects.all()
    lookup_field = 'id'

    def get(self, request, id=None):
        return self.retrieve(request, id)

    def put(self, request, id=None):
        cache.delete('Location_queryset')
        return self.update(request, id)

    def delete(self, request, id=None):
        cache.delete('Location_queryset')
        return self.destroy(request, id)
    


class BannerListCreateApiView(generics.ListCreateAPIView):

    serializer_class = BannerSerializer

    def get_queryset(self):
        return cached_queryset('Banner_queryset', lambda: Banner.objects.all(),timeout=3600)
    
    def get(self, request):
        return self.list(request)

    def post(self, request):
        cache.delete('Banner_queryset')
        return self.create(request)
    
    
class BannerRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a Banner.
    Only superusers are allowed to access this view.
    """
    
    permission_classes=[IsSuperuser,IsAuthenticated]
    serializer_class = BannerSerializer
    queryset = Banner.objects.all()
    lookup_field = 'id'

    def get(self, request, id=None):
        return self.retrieve(request, id)

    def put(self, request, id=None):
        cache.delete('Banner_queryset')
        return self.update(request, id)
    
    def patch(self, request, id=None):
        cache.delete('Banner_queryset')
        return self.partial_update(request, id)


    def delete(self, request, id=None):
        cache.delete('Banner_queryset')
        return self.destroy(request, id)
    

    

class AdminDashboardView(APIView):
    """
    API view for the admin dashboard.
    This view provides statistics about the system including counts of completed events, total events, total users,
    total vendors, total categories, and a list of the latest 5 new events.
    """
    def get(self, request):

        data = cache.get('admin_dashboard_data')
        if data is not None:
            print('fetched from cache')

        if data is None:
            print('fetched from db')
        
            completed_events = Event.objects.filter(status='completed').count()
            total_events = Event.objects.count()
            total_users = CustomUser.objects.count()
            total_vendors = CustomUser.objects.filter(is_vendor=True).count()
            total_categories = Category.objects.count()

            new_events = cached_queryset(
                'admin_event_listing',
                lambda: Event.objects.select_related(
                        'venue','location'
                    ).prefetch_related(
                        'categories','ticket_types','vendor'
                    ).order_by('-start_date'),
                timeout=3600
            )

        # Serialize data
            serializer = EventSerializer(new_events, many=True, context={'request': request})

            data = {
                'completed_events': completed_events,
                'total_events': total_events,
                'total_users': total_users,
                'total_vendors': total_vendors,
                'total_categories': total_categories,
                'new_events': serializer.data,
            }

            cache.set('admin_dashboard_data', data, timeout=3600) 


        return Response(data)
    


class VendorListView(generics.ListAPIView):
    """
    API view to list all vendors.
    """
    serializer_class = VendorSerializer

    def get_queryset(self):
        return cached_queryset(
            'vendors_list', lambda:Vendor.objects.all().select_related('user'), timeout=60
        )
    
    def get(self, request):
        return self.list(request)
    

class BlockUnblockVendorView(APIView):
    """
    API view to block or unblock a user.
    """

    def get(self, request, user_id):
        try:
            vendor = CustomUser.objects.get(id=user_id, is_vendor=True)
        except CustomUser.DoesNotExist:
            return Response({"error": constants.ERROR_VENDOR_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(vendor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, user_id):
        try:
            vendor = CustomUser.objects.get(id=user_id, is_vendor=True)
        except CustomUser.DoesNotExist:
            return Response({"error": constants.ERROR_VENDOR_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        vendor.is_active = not vendor.is_active

        vendor.save(update_fields=['is_active'])
        cache.delete('vendors_list')


        # Prepare response message
        if vendor.is_active:
            message = constants.MESSAGE_VENDOR_UNBLOCKED
        else:
            message = constants.MESSAGE_VENDOR_BLOCKED

        return Response({"message": message}, status=status.HTTP_200_OK)
    



class CustomUserListView(generics.ListAPIView):
    """
    API view to list all vendors.
    """
    serializer_class = UserSerializer

    def get_queryset(self):
        return cached_queryset(
            'users_list', lambda:CustomUser.objects.all(), timeout=60
        )
    
    def get(self, request):
        return self.list(request)
    

class BlockUnblockUserView(APIView):
    """
    API view to block or unblock a user.
    """

    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": constants.ERROR_USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": constants.ERROR_USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        # Toggle the is_active field
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])

        # Prepare response message
        if user.is_active:
            message = constants.MESSAGE_USER_UNBLOCKED
        else:
            message = constants.MESSAGE_USER_BLOCKED

        return Response({
            "message": message,
            "is_active": user.is_active
        }, status=status.HTTP_200_OK)