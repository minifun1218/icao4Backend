"""
MCQ 路由配置
"""
from django.urls import path
from .views import (
    McqQuestionListView,
    McqQuestionDetailView,
    McqQuestionChoicesView,
    McqChoiceListView,
    McqResponseListView,
    McqResponseDetailView,
)

app_name = 'mcq'

urlpatterns = [
    # Question 路由
    path('question/list/', McqQuestionListView.as_view(), name='question-list'),
    path('question/detail/<int:pk>/', McqQuestionDetailView.as_view(), name='question-detail'),
    path('question/<int:question_id>/choices/', McqQuestionChoicesView.as_view(), name='question-choices'),
    
    # Choice 路由
    path('choice/list/', McqChoiceListView.as_view(), name='choice-list'),
    
    # Response 路由
    path('response/list/', McqResponseListView.as_view(), name='response-list'),
    path('response/detail/<int:pk>/', McqResponseDetailView.as_view(), name='response-detail'),
]
