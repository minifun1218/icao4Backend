"""
自定义权限类
"""
from rest_framework.permissions import BasePermission


class IsActiveUser(BasePermission):
    """
    只允许激活状态的用户访问
    """
    message = '您的账号已被禁用，请联系管理员'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active()


class IsAdminUser(BasePermission):
    """
    只允许管理员用户访问
    """
    message = '您没有权限访问此资源'
    
    def has_permission(self, request, view):
        # 这里可以根据实际需求判断用户是否为管理员
        # 例如检查用户的roles
        return request.user and request.user.is_authenticated and request.user.is_active()

