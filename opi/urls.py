"""
OPI 路由配置
"""
from django.urls import path
from .views import (
    OpiQuestionsView,
    OpiQuestionsAllView,
    OpiSubmitAnswerView,
    OpiTopicListView,
    OpiTopicDetailView,
    OpiQuestionListView,
    OpiResponseListView,
)

app_name = 'opi'

urlpatterns = [
    # 获取题目（支持顺序/随机模式）- 类似 mcq
    path('questions', OpiQuestionsView.as_view(), name='questions-no-slash'),
    
    # 获取所有口语面试模块及用户答题情况 - 类似 mcq
    path('questions/all/', OpiQuestionsAllView.as_view(), name='questions-all'),
    
    # 提交答题 - 类似 mcq
    path('submit/', OpiSubmitAnswerView.as_view(), name='submit-answer'),
    
    # Topic 路由（旧接口，保留兼容）
    path('topic/list/', OpiTopicListView.as_view(), name='topic-list'),
    path('topic/detail/<int:pk>/', OpiTopicDetailView.as_view(), name='topic-detail'),
    
    # Question 路由（旧接口，保留兼容）
    path('question/list/', OpiQuestionListView.as_view(), name='question-list'),
    
    # Response 路由（旧接口，保留兼容）
    path('response/list/', OpiResponseListView.as_view(), name='response-list'),
]
