"""
账号相关URL配置
"""
from django.urls import path
from .views import (
    WxLoginView, 
    UserInfoView, 
    TokenRefreshView,
    UserStatsView,
    UserLearningProgressView
)

app_name = 'account'

urlpatterns = [
    # 微信登录
    path('wxlogin/', WxLoginView.as_view(), name='wx-login'),
    
    # 用户信息
    path('info/', UserInfoView.as_view(), name='user-info'),
    
    # Token刷新
    path('token-refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # 用户学习统计
    path('stats/', UserStatsView.as_view(), name='user-stats'),
    
    # 学习进度
    path('learning-progress/', UserLearningProgressView.as_view(), name='learning-progress'),
]
