"""
ATC 路由配置
"""
from django.urls import path
from .views import (
    # Airport views
    AirportListView,
    AirportDetailView,
    AirportByIcaoView,
    
    # AtcScenario views
    AtcScenarioListView,
    AtcScenarioDetailView,
    AtcScenarioActiveListView,
    AtcScenarioSearchView,
    
    # AtcTurn views
    AtcTurnListView,
    AtcTurnDetailView,
    AtcTurnsByScenarioView,
)

app_name = 'atc'

urlpatterns = [
    # ==================== Airport 路由 ====================
    # 机场列表（分页查询）
    path('airport/list/', AirportListView.as_view(), name='airport-list'),
    
    # 机场详情
    path('airport/detail/<int:pk>/', AirportDetailView.as_view(), name='airport-detail'),
    
    # 通过ICAO代码查询机场
    path('airport/icao/<str:icao>/', AirportByIcaoView.as_view(), name='airport-by-icao'),
    
    # ==================== AtcScenario 路由 ====================
    # 场景列表（分页查询）
    path('scenario/list/', AtcScenarioListView.as_view(), name='scenario-list'),
    
    # 场景详情
    path('scenario/detail/<int:pk>/', AtcScenarioDetailView.as_view(), name='scenario-detail'),
    
    # 获取激活的场景（前端展示用）
    path('scenario/active/', AtcScenarioActiveListView.as_view(), name='scenario-active'),
    
    # 场景搜索
    path('scenario/search/', AtcScenarioSearchView.as_view(), name='scenario-search'),
    
    # 获取指定场景的所有轮次
    path('scenario/<int:scenario_id>/turns/', AtcTurnsByScenarioView.as_view(), name='scenario-turns'),
    
    # ==================== AtcTurn 路由 ====================
    # 轮次列表（分页查询）
    path('turn/list/', AtcTurnListView.as_view(), name='turn-list'),
    
    # 轮次详情
    path('turn/detail/<int:pk>/', AtcTurnDetailView.as_view(), name='turn-detail'),
]

