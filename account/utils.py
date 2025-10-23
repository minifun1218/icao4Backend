"""
认证相关工具函数
"""
import requests
from django.conf import settings


def get_wechat_session(code):
    """
    通过微信code获取session_key和openid
    
    Args:
        code: 微信小程序login接口返回的code
    
    Returns:
        dict: 包含openid, session_key等信息，失败返回None
    """
    app_id = settings.WECHAT_MINI_PROGRAM.get('APP_ID')
    app_secret = settings.WECHAT_MINI_PROGRAM.get('APP_SECRET')
    login_url = settings.WECHAT_MINI_PROGRAM.get('LOGIN_URL')
    
    if not app_id or not app_secret:
        raise ValueError('微信小程序配置不完整，请检查APP_ID和APP_SECRET')
    
    params = {
        'appid': app_id,
        'secret': app_secret,
        'js_code': code,
        'grant_type': 'authorization_code'
    }
    
    try:
        response = requests.get(login_url, params=params, timeout=10)
        result = response.json()
        
        if 'errcode' in result and result['errcode'] != 0:
            # 微信接口返回错误
            return None
        
        return result
    except Exception as e:
        print(f"微信登录请求失败: {str(e)}")
        return None

