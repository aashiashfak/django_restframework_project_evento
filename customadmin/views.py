from .serializers import (
    SuperuserLoginSerializer,
    CategorySerializer,
    LocationSerializer
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import generics, mixins
from .models import Category,Location
from accounts.permissions import IsSuperuser
from rest_framework.permissions import IsAuthenticated

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

    permission_classes=[IsSuperuser,IsAuthenticated]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def get(self, request):
        return self.list(request)

    def post(self, request):
        return self.create(request)
    
class CategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):

    permission_classes=[IsSuperuser,IsAuthenticated]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    lookup_field = 'id'

    def get(self, request, id=None):
        return self.retrieve(request, id)

    def put(self, request, id=None):
        return self.update(request, id)

    def delete(self, request, id=None):
        return self.destroy(request, id)


class LocationListCreateAPIView(generics.ListCreateAPIView):

    permission_classes=[IsSuperuser,IsAuthenticated]
    serializer_class = LocationSerializer
    queryset = Location.objects.all()

    def get(self, request):
        return self.list(request)

    def post(self, request):
        return self.create(request)
    
class LocationRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):

    permission_classes=[IsSuperuser,IsAuthenticated]
    serializer_class = LocationSerializer
    queryset = Location.objects.all()
    lookup_field = 'id'

    def get(self, request, id=None):
        return self.retrieve(request, id)

    def put(self, request, id=None):
        return self.update(request, id)

    def delete(self, request, id=None):
        return self.destroy(request, id)