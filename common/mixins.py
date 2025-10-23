"""
通用Mixin类
"""
from .response import ApiResponse


class ResponseMixin:
    """
    响应Mixin - 为视图类添加统一响应方法
    """
    
    def success_response(self, data=None, message='success', code=200):
        """成功响应"""
        return ApiResponse.success(data=data, message=message, code=code)
    
    def error_response(self, message='error', code=400, data=None):
        """错误响应"""
        return ApiResponse.error(message=message, code=code, data=data)
    
    def bad_request_response(self, message='请求参数错误', data=None):
        """400 参数错误"""
        return ApiResponse.bad_request(message=message, data=data)
    
    def unauthorized_response(self, message='未授权，请先登录', data=None):
        """401 未授权"""
        return ApiResponse.unauthorized(message=message, data=data)
    
    def forbidden_response(self, message='权限不足', data=None):
        """403 禁止访问"""
        return ApiResponse.forbidden(message=message, data=data)
    
    def not_found_response(self, message='资源不存在', data=None):
        """404 未找到"""
        return ApiResponse.not_found(message=message, data=data)
    
    def server_error_response(self, message='服务器内部错误', data=None):
        """500 服务器错误"""
        return ApiResponse.server_error(message=message, data=data)

