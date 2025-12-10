"""
Custom permission classes for API endpoints.
Role-based permissions for different API resources.
"""
from rest_framework import permissions
from functools import wraps


class IsAdminOrDepo(permissions.BasePermission):
    """Admin veya Depo kullanıcıları için izin"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_groups = request.user.groups.values_list('name', flat=True)
        return request.user.is_superuser or 'Admin' in user_groups or 'Depo' in user_groups


class IsAdminOrMuhasebe(permissions.BasePermission):
    """Admin veya Muhasebe kullanıcıları için izin"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_groups = request.user.groups.values_list('name', flat=True)
        return request.user.is_superuser or 'Admin' in user_groups or 'Muhasebe' in user_groups


class IsAdminOrSatis(permissions.BasePermission):
    """Admin veya Satış kullanıcıları için izin"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_groups = request.user.groups.values_list('name', flat=True)
        return request.user.is_superuser or 'Admin' in user_groups or 'Satış' in user_groups


class IsAdminOrMudur(permissions.BasePermission):
    """Admin veya Müdür kullanıcıları için izin"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_groups = request.user.groups.values_list('name', flat=True)
        return request.user.is_superuser or 'Admin' in user_groups or 'Müdür' in user_groups


class IsAdminOnly(permissions.BasePermission):
    """Sadece Admin kullanıcıları için izin"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_groups = request.user.groups.values_list('name', flat=True)
        return request.user.is_superuser or 'Admin' in user_groups

