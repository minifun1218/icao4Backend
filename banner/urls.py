"""
Banner 路由配置
"""
from django.urls import path
from .views import (
    BannerListView,
    BannerDetailView,
    BannerActiveListView,
    BannerItemListView,
    BannerSearchView,
    BannerItemAllListView
)

app_name = 'banner'

urlpatterns = [
    # 所有BannerItem列表（分页查询） - 显示所有轮播图项目
    path('list/', BannerItemAllListView.as_view(), name='banneritem-list'),
    
    # Banner组列表（分页查询）
    path('banners/', BannerListView.as_view(), name='banner-list'),
    
    # Banner详情
    path('detail/<int:pk>/', BannerDetailView.as_view(), name='banner-detail'),
    
    # 获取当前应该显示的Banner（前端展示用）
    path('active/', BannerActiveListView.as_view(), name='banner-active'),
    
    # 获取指定Banner的所有项目
    path('<int:banner_id>/items/', BannerItemListView.as_view(), name='banner-items'),
    
    # Banner搜索
    path('search/', BannerSearchView.as_view(), name='banner-search'),
]
