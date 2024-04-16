from django.urls import path
from .views import (
    SuperUserLoginView,
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
    LocationListCreateAPIView,
    LocationRetrieveUpdateDestroyAPIView,


)

urlpatterns = [
    path('login/', SuperUserLoginView.as_view(), name='superuser-login'),
    path('categories/', CategoryListCreateAPIView.as_view(), name='category_list_create'),
    path('categories/<int:id>/', CategoryRetrieveUpdateDestroyAPIView.as_view(), name='category_retrieve_update_destroy'),
    path('Locations/', LocationListCreateAPIView.as_view(), name='category_list_create'),
    path('Locations/<int:id>/', LocationRetrieveUpdateDestroyAPIView.as_view(), name='category_retrieve_update_destroy'),
    
]
