from rest_framework import permissions

class IsVendor(permissions.BasePermission):
    """
    Custom permission to check if the authenticated user is a vendor.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_vendor

class IsSuperuser(permissions.BasePermission):
    """
    Custom permission to check if the authenticated user is a Customsuperuser.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser 



class IsActiveUser(permissions.BasePermission):
    """
    Custom permission to allow access only to active users.
    """

    def has_permission(self, request, view):
        return request.user.is_active