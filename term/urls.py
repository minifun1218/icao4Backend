"""
Term 路由配置
"""
from django.urls import path
from .views import (
    AvTermsTopicListView,
    AvTermsTopicDetailView,
    AvTermListView,
    AvTermDetailView,
    AvTermSearchView,
    AvTermStatsView,
    TermMarkView,
)

app_name = 'term'

urlpatterns = [
    # Topic 路由
    path('topic/list/', AvTermsTopicListView.as_view(), name='topic-list'),
    path('topics/', AvTermsTopicListView.as_view(), name='topics-list'),  # topics别名
    path('topics', AvTermsTopicListView.as_view(), name='topics-list-no-slash'),  # 无斜杠版本
    path('themes/', AvTermsTopicListView.as_view(), name='themes-list'),  # themes别名
    path('themes', AvTermsTopicListView.as_view(), name='themes-list-no-slash'),  # 无斜杠版本，兼容前端
    path('topic/detail/<int:pk>/', AvTermsTopicDetailView.as_view(), name='topic-detail'),
    path('theme/<int:pk>/', AvTermsTopicDetailView.as_view(), name='theme-detail'),  # theme单数别名，返回主题下的术语列表
    
    # Term 路由
    path('term/list/', AvTermListView.as_view(), name='term-list'),
    path('term/detail/<int:pk>/', AvTermDetailView.as_view(), name='term-detail'),
    path('term/search/', AvTermSearchView.as_view(), name='term-search'),
    
    # 统计接口
    path('stats/', AvTermStatsView.as_view(), name='term-stats'),
    path('stats', AvTermStatsView.as_view(), name='term-stats-no-slash'),  # 无斜杠版本，兼容前端
    
    # 标记接口
    path('mark/', TermMarkView.as_view(), name='term-mark'),
    path('mark', TermMarkView.as_view(), name='term-mark-no-slash'),  # 无斜杠版本，兼容前端
]
