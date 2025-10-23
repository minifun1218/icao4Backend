"""
自定义JWT认证
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from .models import WxUser


class WxUserJWTAuthentication(JWTAuthentication):
    """
    自定义JWT认证类，使用WxUser而不是Django默认User
    """
    
    def get_user(self, validated_token):
        """
        根据token中的user_id获取WxUser对象
        """
        try:
            user_id = validated_token.get('user_id')
            if user_id is None:
                raise InvalidToken(_('Token contained no recognizable user identification'))
            
            # 使用WxUser模型查找用户
            user = WxUser.objects.get(id=user_id)
            
            # 检查用户状态
            if user.status != 1:
                raise AuthenticationFailed(_('User is inactive'))
            
            return user
            
        except WxUser.DoesNotExist:
            raise AuthenticationFailed(_('User not found'))
        except Exception as e:
            raise InvalidToken(_(f'Invalid token: {str(e)}'))
