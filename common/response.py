"""
统一响应格式
"""
from rest_framework.response import Response
from rest_framework import status


class ApiResponse:
    """
    统一API响应类
    格式：
    {
        "code": 状态码,
        "message": 消息,
        "data": 数据
    }
    """
    
    @staticmethod
    def success(data=None, message='success', code=200):
        """
        成功响应
        
        Args:
            data: 返回的数据
            message: 提示消息
            code: 业务状态码
        
        Returns:
            Response对象
        """
        return Response({
            'code': code,
            'message': message,
            'data': data if data is not None else {}
        }, status=status.HTTP_200_OK)
    
    @staticmethod
    def error(message='error', code=400, data=None):
        """
        错误响应
        
        Args:
            message: 错误消息
            code: 业务状态码
            data: 错误详情数据
        
        Returns:
            Response对象
        """
        return Response({
            'code': code,
            'message': message,
            'data': data if data is not None else {}
        }, status=status.HTTP_200_OK)
    
    @staticmethod
    def bad_request(message='请求参数错误', data=None):
        """400 参数错误"""
        return ApiResponse.error(message=message, code=400, data=data)
    
    @staticmethod
    def unauthorized(message='未授权，请先登录', data=None):
        """401 未授权"""
        return ApiResponse.error(message=message, code=401, data=data)
    
    @staticmethod
    def forbidden(message='权限不足', data=None):
        """403 禁止访问"""
        return ApiResponse.error(message=message, code=403, data=data)
    
    @staticmethod
    def not_found(message='资源不存在', data=None):
        """404 未找到"""
        return ApiResponse.error(message=message, code=404, data=data)
    
    @staticmethod
    def server_error(message='服务器内部错误', data=None):
        """500 服务器错误"""
        return ApiResponse.error(message=message, code=500, data=data)


def create_response(code=200, message='success', data=None):
    """
    快捷创建响应的函数
    
    Args:
        code: 状态码
        message: 消息
        data: 数据
    
    Returns:
        Response对象
    """
    return Response({
        'code': code,
        'message': message,
        'data': data if data is not None else {}
    }, status=status.HTTP_200_OK)

