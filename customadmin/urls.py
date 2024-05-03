from django.urls import path
from .views import (
    SuperUserLoginView,
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
    LocationListCreateAPIView,
    LocationRetrieveUpdateDestroyAPIView,
    AdminDashboardView,
    VendorListView,
    BlockUnblockVendorView,
    CustomUserListView,
    BlockUnblockUserView
    
    
)

urlpatterns = [
    path('login/', SuperUserLoginView.as_view(), name='superuser-login'),
    path('categories/', CategoryListCreateAPIView.as_view(), name='category_list_create'),
    path('categories/<int:id>/', CategoryRetrieveUpdateDestroyAPIView.as_view(), name='category_retrieve_update_destroy'),
    path('Locations/', LocationListCreateAPIView.as_view(), name='category_list_create'),
    path('Locations/<int:id>/', LocationRetrieveUpdateDestroyAPIView.as_view(), name='category_retrieve_update_destroy'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('vendors-list/', VendorListView.as_view(), name='vendor-list'),
    path('vendor/<int:user_id>/', BlockUnblockVendorView.as_view(), name='vendor-detail'),
    path('users-list/', CustomUserListView.as_view(), name='user-list'),
    path('user/<int:user_id>/', BlockUnblockUserView.as_view(), name='user-detail'),
]
