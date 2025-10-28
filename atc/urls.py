"""
ATC 路由配置
"""
from django.urls import path
from .views import (
    # ATC Questions views (类似 MCQ)
    AtcQuestionsView,
    AtcQuestionsAllView,
    AtcSubmitAnswerView,
    
)

app_name = 'atc'

urlpatterns = [
    # ==================== ATC Questions 路由（类似 MCQ）====================
    # 获取题目（支持顺序/随机模式）- 类似 mcq
    path('questions', AtcQuestionsView.as_view(), name='questions-no-slash'),
    
    # 获取所有ATC通讯模块及用户答题情况 - 类似 mcq
    path('questions/all/', AtcQuestionsAllView.as_view(), name='questions-all'),
    
    # 提交答题 - 类似 mcq
    path('submit/', AtcSubmitAnswerView.as_view(), name='submit-answer'),
    

]

