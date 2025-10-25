"""
MCQ 路由配置
"""
from django.urls import path
from .views import (
    McqQuestionsView,
    McqQuestionsAllView,
    McqSubmitAnswerView,
    McqUserProgressView,
)

app_name = 'mcq'

urlpatterns = [
    # 获取题目（支持顺序/随机模式）
    path('questions', McqQuestionsView.as_view(), name='questions-no-slash'),
    
    # 获取所有听力理解模块及用户答题情况
    path('questions/all/', McqQuestionsAllView.as_view(), name='questions-all'),
    
    # 提交答题
    path('submit/', McqSubmitAnswerView.as_view(), name='submit-answer'),
    
    # 获取用户在指定模块的答题进度
    path('progress/<int:module_id>/', McqUserProgressView.as_view(), name='user-progress'),
]
