from django.urls import path
from .views import EventListAPIView

urlpatterns = [
    path('listAllEvents/', EventListAPIView.as_view(), name='event-list'),
]