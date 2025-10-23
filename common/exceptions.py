"""
自定义异常处理
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    自定义异常处理器 - 统一返回格式
    """
    # 调用DRF默认的异常处理器
    response = exception_handler(exc, context)
    
    if response is not None:
        # 获取状态码
        status_code = response.status_code
        
        # 根据HTTP状态码映射业务消息
        message_map = {
            400: '请求参数错误',
            401: '未授权，请先登录',
            403: '权限不足，无法访问',
            404: '资源不存在',
            405: '请求方法不允许',
            500: '服务器内部错误',
        }
        
        # 获取默认消息
        message = message_map.get(status_code, '请求失败')
        
        # 提取详细错误信息
        error_data = {}
        
        if isinstance(response.data, dict):
            # 如果有detail字段，使用它作为消息
            if 'detail' in response.data:
                message = str(response.data['detail'])
            # 如果有non_field_errors，使用第一个作为消息
            elif 'non_field_errors' in response.data:
                message = str(response.data['non_field_errors'][0])
            # 其他字段错误
            else:
                # 检查是否有字段验证错误
                has_field_errors = any(
                    key not in ['detail', 'code', 'message', 'data'] 
                    for key in response.data.keys()
                )
                if has_field_errors:
                    error_data = response.data
                    # 如果没有设置message，使用第一个字段的错误
                    if message == message_map.get(status_code, '请求失败'):
                        first_error_field = next(iter(response.data.keys()))
                        first_error_value = response.data[first_error_field]
                        if isinstance(first_error_value, list) and first_error_value:
                            message = str(first_error_value[0])
        elif isinstance(response.data, list) and response.data:
            # 如果是列表，取第一个作为消息
            message = str(response.data[0])
        else:
            # 其他情况，转换为字符串
            message = str(response.data)
        
        # 统一格式
        response.data = {
            'code': status_code,
            'message': message,
            'data': error_data
        }
    
    return response

