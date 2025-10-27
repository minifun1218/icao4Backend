"""
Story 路由配置
"""
from django.urls import path
from .views import (
    RetellQuestionsView,
    RetellQuestionsAllView,
    RetellSubmitAnswerView,
    RetellItemListView,
    RetellItemDetailView,
    RetellResponseListView,
    RetellModulesListView,
)

app_name = 'story'

urlpatterns = [
    # 获取题目（支持顺序/随机模式）- 类似 mcq
    path('questions', RetellQuestionsView.as_view(), name='questions-no-slash'),
    
    # 获取所有故事复述模块及用户答题情况 - 类似 mcq
    path('questions/all/', RetellQuestionsAllView.as_view(), name='questions-all'),
    
    # 提交答题 - 类似 mcq
    path('submit/', RetellSubmitAnswerView.as_view(), name='submit-answer'),
    
    # 以模块为单位的列表（旧接口，保留兼容）
    path('list/', RetellModulesListView.as_view(), name='modules-list'),
    
    # 原有的题目列表接口（保留兼容）
    path('item/list/', RetellItemListView.as_view(), name='item-list'),
    path('item/detail/<int:pk>/', RetellItemDetailView.as_view(), name='item-detail'),
    
    # 答题记录列表（保留兼容）
    path('response/list/', RetellResponseListView.as_view(), name='response-list'),
]
