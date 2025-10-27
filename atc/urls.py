"""
ATC 路由配置
"""
from django.urls import path
from .views import (
    # ATC Questions views (类似 MCQ)
    AtcQuestionsView,
    AtcQuestionsAllView,
    AtcSubmitAnswerView,
    
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
    # ==================== ATC Questions 路由（类似 MCQ）====================
    # 获取题目（支持顺序/随机模式）- 类似 mcq
    path('questions', AtcQuestionsView.as_view(), name='questions-no-slash'),
    
    # 获取所有ATC通讯模块及用户答题情况 - 类似 mcq
    path('questions/all/', AtcQuestionsAllView.as_view(), name='questions-all'),
    
    # 提交答题 - 类似 mcq
    path('submit/', AtcSubmitAnswerView.as_view(), name='submit-answer'),
    
    # ==================== Airport 路由（旧接口，保留兼容）====================
    # 机场列表（分页查询）
    path('airport/list/', AirportListView.as_view(), name='airport-list'),
    
    # 机场详情
    path('airport/detail/<int:pk>/', AirportDetailView.as_view(), name='airport-detail'),
    
    # 通过ICAO代码查询机场
    path('airport/icao/<str:icao>/', AirportByIcaoView.as_view(), name='airport-by-icao'),
    
    # ==================== AtcScenario 路由（旧接口，保留兼容）====================
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
    
    # ==================== AtcTurn 路由（旧接口，保留兼容）====================
    # 轮次列表（分页查询）
    path('turn/list/', AtcTurnListView.as_view(), name='turn-list'),
    
    # 轮次详情
    path('turn/detail/<int:pk>/', AtcTurnDetailView.as_view(), name='turn-detail'),
]

