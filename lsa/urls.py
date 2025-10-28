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
    # 获取题目（支持顺序/随机模式）
    path('questions', LsaQuestionsView.as_view(), name='questions-no-slash'),
    
    # 获取所有听力简答模块及用户答题情况
    path('questions/all/', LsaQuestionsAllView.as_view(), name='questions-all'),
    
    # 提交答题
    path('submit/', LsaSubmitAnswerView.as_view(), name='submit-answer'),

]
