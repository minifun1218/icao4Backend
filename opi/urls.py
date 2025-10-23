"""
OPI 路由配置
"""
from django.urls import path
from .views import (
    OpiTopicListView,
    OpiTopicDetailView,
    OpiQuestionListView,
    OpiResponseListView,
)

app_name = 'opi'

urlpatterns = [
    path('topic/list/', OpiTopicListView.as_view(), name='topic-list'),
    path('topic/detail/<int:pk>/', OpiTopicDetailView.as_view(), name='topic-detail'),
    path('question/list/', OpiQuestionListView.as_view(), name='question-list'),
    path('response/list/', OpiResponseListView.as_view(), name='response-list'),
]
