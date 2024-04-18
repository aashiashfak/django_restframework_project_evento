from rest_framework import permissions

class IsVendor(permissions.BasePermission):
    """
    Custom permission to check if the authenticated user is a vendor.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_vendor