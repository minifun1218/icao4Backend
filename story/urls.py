"""
Story 路由配置
"""
from django.urls import path
from .views import (
    RetellQuestionsView,
    RetellQuestionsAllView,
    RetellSubmitAnswerView,

)

app_name = 'story'

urlpatterns = [
    # 获取题目（支持顺序/随机模式）
    path('questions', RetellQuestionsView.as_view(), name='questions-no-slash'),
    
    # 获取所有故事复述模块及用户答题情况 -
    path('questions/all/', RetellQuestionsAllView.as_view(), name='questions-all'),
    
    # 提交答题
    path('submit/', RetellSubmitAnswerView.as_view(), name='submit-answer'),
    

]
