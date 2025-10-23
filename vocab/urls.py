"""
Vocab 路由配置
"""
from django.urls import path
from .views import (
    AvVocabTopicListView,
    AvVocabTopicDetailView,
    AvVocabListView,
    AvVocabDetailView,
    AvVocabSearchView,
    AvVocabStatsView,
    UserVocabLearningView,
    UserTermLearningView,
    UserLearningStatsView,
    VocabMarkView,
    VocabQuickActionView,
    TermQuickActionView,
)

app_name = 'vocab'

urlpatterns = [
    # Topic 路由
    path('topic/list/', AvVocabTopicListView.as_view(), name='topic-list'),
    path('topic/detail/<int:pk>/', AvVocabTopicDetailView.as_view(), name='topic-detail'),
    path('themes', AvVocabTopicListView.as_view(), name='themes'),  # themes别名，兼容前端
    path('theme/<int:pk>/', AvVocabTopicDetailView.as_view(), name='theme-detail'),  # theme单数别名
    
    # Vocab 路由
    path('vocab/list/', AvVocabListView.as_view(), name='vocab-list'),
    path('vocab/detail/<int:pk>/', AvVocabDetailView.as_view(), name='vocab-detail'),
    path('vocab/search/', AvVocabSearchView.as_view(), name='vocab-search'),
    
    # 统计接口
    path('stats', AvVocabStatsView.as_view(), name='vocab-stats'),
    
    # 学习记录接口
    path('learning/vocab/', UserVocabLearningView.as_view(), name='user-vocab-learning'),
    path('learning/term/', UserTermLearningView.as_view(), name='user-term-learning'),
    path('learning/stats/', UserLearningStatsView.as_view(), name='user-learning-stats'),
    
    # 统一标记接口（推荐使用）
    path('mark/', VocabMarkView.as_view(), name='vocab-mark'),
    
    # 快速操作接口（RESTful风格，可选）
    path('quick-action/<int:vocab_id>/<str:action>/', VocabQuickActionView.as_view(), name='vocab-quick-action'),
    path('quick-action/term/<int:term_id>/<str:action>/', TermQuickActionView.as_view(), name='term-quick-action'),
]
