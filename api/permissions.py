from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Разрешает доступ администраторам, суперпользователям и персоналу"""
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (
            user.is_admin
            or user.is_superuser
            or user.is_staff
        )


class IsAdminOrReadOnly(IsAdmin):
    """
    Разрешает полный доступ администраторам и доступ на чтение всем остальным.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return super().has_permission(request, view)


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет автору объекта, администраторам и модераторам
    редактировать объекты. Всем остальным разрешен только просмотр.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        is_author = obj.author == request.user
        is_admin = request.user.is_admin
        is_moderator = request.user.is_moderator
        return is_author or is_admin or is_moderator

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)
