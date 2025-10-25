"""
Story 路由配置
"""
from django.urls import path
from .views import (
    RetellItemListView,
    RetellItemDetailView,
    RetellResponseListView,
    RetellModulesListView,
)

app_name = 'story'

urlpatterns = [
    # 以模块为单位的列表（新接口）
    path('list/', RetellModulesListView.as_view(), name='modules-list'),
    
    # 原有的题目列表接口
    path('item/list/', RetellItemListView.as_view(), name='item-list'),
    path('item/detail/<int:pk>/', RetellItemDetailView.as_view(), name='item-detail'),
    
    # 答题记录列表
    path('response/list/', RetellResponseListView.as_view(), name='response-list'),
]
