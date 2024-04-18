from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import Event
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Event
from .serializers import EventCreateSerializer
from accounts.permissions import IsVendor
from rest_framework.permissions import IsAuthenticated

class VendorEventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()  # This is just a placeholder, will be overridden by get_queryset
    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated, IsVendor]

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user)  # Assign the current user as the vendor

    def perform_update(self, serializer):
        serializer.save(vendor=self.request.user)  # Ensure the current user is the vendor

    def get_queryset(self):
        return Event.objects.filter(vendor=self.request.user)