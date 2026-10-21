from rest_framework import permissions


class IsAdminOrOnlyRead(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.user and request.user.is_staff) or (
            request.method in permissions.SAFE_METHODS
        )
