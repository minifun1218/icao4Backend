"""
Media 路由配置
"""
from django.urls import path
from .views import (
    MediaAssetListView,
    MediaAssetDetailView,
    MediaTypeListView,
    MediaAssetsByTypeView,
)

app_name = 'media'

urlpatterns = [
    path('asset/list/', MediaAssetListView.as_view(), name='asset-list'),
    path('asset/detail/<int:pk>/', MediaAssetDetailView.as_view(), name='asset-detail'),
    path('asset/type/<str:media_type>/', MediaAssetsByTypeView.as_view(), name='asset-by-type'),
    path('types/', MediaTypeListView.as_view(), name='type-list'),
]
