"""
LSA 路由配置
"""
from django.urls import path
from .views import (
    LsaQuestionsView,
    LsaQuestionsAllView,
    LsaSubmitAnswerView,
    LsaDialogListView,
    LsaDialogDetailView,
    LsaDialogQuestionsView,
    LsaQuestionListView,
    LsaQuestionDetailView,
    LsaResponseListView,
)

app_name = 'lsa'

urlpatterns = [
    # 获取题目（支持顺序/随机模式）- 类似 mcq
    path('questions', LsaQuestionsView.as_view(), name='questions-no-slash'),
    
    # 获取所有听力简答模块及用户答题情况 - 类似 mcq
    path('questions/all/', LsaQuestionsAllView.as_view(), name='questions-all'),
    
    # 提交答题 - 类似 mcq
    path('submit/', LsaSubmitAnswerView.as_view(), name='submit-answer'),
    
    # Dialog 路由（旧接口，保留兼容）
    path('dialog/list/', LsaDialogListView.as_view(), name='dialog-list'),
    path('dialog/detail/<int:pk>/', LsaDialogDetailView.as_view(), name='dialog-detail'),
    path('dialog/<int:dialog_id>/questions/', LsaDialogQuestionsView.as_view(), name='dialog-questions'),
    
    # Question 路由（旧接口，保留兼容）
    path('question/list/', LsaQuestionListView.as_view(), name='question-list'),
    path('question/detail/<int:pk>/', LsaQuestionDetailView.as_view(), name='question-detail'),
    
    # Response 路由（旧接口，保留兼容）
    path('response/list/', LsaResponseListView.as_view(), name='response-list'),
]
