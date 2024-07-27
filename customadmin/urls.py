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
    BlockUnblockUserView,
    BannerListCreateApiView,
    BannerRetrieveUpdateDestroyAPIView
    
    
)

urlpatterns = [
    path('login/', SuperUserLoginView.as_view(), name='superuser-login'),
    path('categories/', CategoryListCreateAPIView.as_view(), name='category_list_create'),
    path('categories/<int:id>/', CategoryRetrieveUpdateDestroyAPIView.as_view(), name='category_retrieve_update_destroy'),
    path('locations/', LocationListCreateAPIView.as_view(), name='Location_list_create'),
    path('locations/<int:id>/', LocationRetrieveUpdateDestroyAPIView.as_view(), name='Location_retrieve_update_destroy'),
    path('banners/', BannerListCreateApiView.as_view(), name='Banner_list_create'),
    path('banners/<int:id>/', BannerRetrieveUpdateDestroyAPIView.as_view(), name='Banner_retrieve_update_destroy'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('vendors-list/', VendorListView.as_view(), name='vendor-list'),
    path('vendor/<int:user_id>/', BlockUnblockVendorView.as_view(), name='vendor-detail'),
    path('users-list/', CustomUserListView.as_view(), name='user-list'),
    path('user/<int:user_id>/', BlockUnblockUserView.as_view(), name='user-detail'),
]
