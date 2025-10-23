"""
Exam 路由配置
"""
from django.urls import path
from .views import (
    # ExamPaper views
    ExamPaperListView,
    ExamPaperDetailView,
    ExamPaperByCodeView,
    ExamPaperSearchView,
    ExamPaperModulesView,
    
    # ExamModule views
    ExamModuleListView,
    ExamModuleDetailView,
    ExamModuleTypesView,
)

app_name = 'exam'

urlpatterns = [
    # ==================== ExamPaper 路由 ====================
    # 试卷列表（分页查询）
    path('paper/list/', ExamPaperListView.as_view(), name='paper-list'),
    
    # 试卷详情
    path('paper/detail/<int:pk>/', ExamPaperDetailView.as_view(), name='paper-detail'),
    
    # 通过试卷代码查询
    path('paper/code/<str:code>/', ExamPaperByCodeView.as_view(), name='paper-by-code'),
    
    # 试卷搜索
    path('paper/search/', ExamPaperSearchView.as_view(), name='paper-search'),
    
    # 获取指定试卷的所有模块
    path('paper/<int:paper_id>/modules/', ExamPaperModulesView.as_view(), name='paper-modules'),
    
    # ==================== ExamModule 路由 ====================
    # 模块列表（分页查询）
    path('module/list/', ExamModuleListView.as_view(), name='module-list'),
    
    # 模块详情
    path('module/detail/<int:pk>/', ExamModuleDetailView.as_view(), name='module-detail'),
    
    # 获取所有模块类型
    path('module/types/', ExamModuleTypesView.as_view(), name='module-types'),
]
