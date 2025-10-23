"""
自定义渲染器 - 统一返回格式
"""
from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    """
    自定义JSON渲染器
    统一所有API响应格式为：
    {
        "code": 状态码,
        "message": 消息,
        "data": 数据
    }
    """
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        重写render方法
        """
        response = renderer_context.get('response') if renderer_context else None
        
        # 如果数据已经是统一格式，直接返回
        if isinstance(data, dict) and 'code' in data and 'message' in data and 'data' in data:
            return super().render(data, accepted_media_type, renderer_context)
        
        # 如果是Django REST framework的异常响应，已经在异常处理器中处理过了
        if response and hasattr(response, 'exception') and response.exception:
            return super().render(data, accepted_media_type, renderer_context)
        
        # 包装成统一格式
        if response:
            status_code = response.status_code
            
            # 成功响应
            if 200 <= status_code < 300:
                formatted_data = {
                    'code': 200,
                    'message': 'success',
                    'data': data if data is not None else {}
                }
            # 错误响应
            else:
                formatted_data = {
                    'code': status_code,
                    'message': self._get_error_message(status_code, data),
                    'data': {}
                }
        else:
            # 默认成功格式
            formatted_data = {
                'code': 200,
                'message': 'success',
                'data': data if data is not None else {}
            }
        
        return super().render(formatted_data, accepted_media_type, renderer_context)
    
    def _get_error_message(self, status_code, data):
        """
        根据状态码和数据获取错误消息
        """
        # 如果data中有detail字段，使用它作为消息
        if isinstance(data, dict):
            if 'detail' in data:
                return str(data['detail'])
            elif 'message' in data:
                return str(data['message'])
        
        # 默认错误消息
        error_messages = {
            400: '请求参数错误',
            401: '未授权，请先登录',
            403: '权限不足',
            404: '资源不存在',
            405: '请求方法不允许',
            500: '服务器内部错误',
        }
        
        return error_messages.get(status_code, '请求失败')

