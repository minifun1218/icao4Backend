"""
Story 路由配置
"""
from django.urls import path
from .views import (
    RetellItemListView,
    RetellItemDetailView,
    RetellResponseListView,
)

app_name = 'story'

urlpatterns = [
    path('item/list/', RetellItemListView.as_view(), name='item-list'),
    path('item/detail/<int:pk>/', RetellItemDetailView.as_view(), name='item-detail'),
    path('response/list/', RetellResponseListView.as_view(), name='response-list'),
]
