"""
LSA 路由配置
"""
from django.urls import path
from .views import (
    LsaDialogListView,
    LsaDialogDetailView,
    LsaDialogQuestionsView,
    LsaQuestionListView,
    LsaQuestionDetailView,
    LsaResponseListView,
)

app_name = 'lsa'

urlpatterns = [
    # Dialog 路由
    path('dialog/list/', LsaDialogListView.as_view(), name='dialog-list'),
    path('dialog/detail/<int:pk>/', LsaDialogDetailView.as_view(), name='dialog-detail'),
    path('dialog/<int:dialog_id>/questions/', LsaDialogQuestionsView.as_view(), name='dialog-questions'),
    
    # Question 路由
    path('question/list/', LsaQuestionListView.as_view(), name='question-list'),
    path('question/detail/<int:pk>/', LsaQuestionDetailView.as_view(), name='question-detail'),
    
    # Response 路由
    path('response/list/', LsaResponseListView.as_view(), name='response-list'),
]
