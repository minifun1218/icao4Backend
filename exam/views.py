"""
Exam 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from common.response import ApiResponse
from common.mixins import ResponseMixin
from .models import ExamPaper, ExamModule
from .serializers import (
    ExamPaperSerializer,
    ExamPaperListSerializer,
    ExamPaperDetailSerializer,
    ExamModuleSerializer,
    ExamModuleDetailSerializer
)


class ExamPagination(PageNumberPagination):
    """
    Exam分页类
    """
    page_size = 10  # 每页显示10条
    page_size_query_param = 'page_size'  # 允许客户端通过page_size参数自定义每页数量
    max_page_size = 100  # 最大每页100条
    page_query_param = 'page'  # 页码参数名


# ==================== ExamPaper 视图 ====================

class ExamPaperListView(APIView, ResponseMixin):
    """
    考试试卷列表视图（分页查询）
    
    GET /api/exam/paper/list/
    Query参数:
        - page: 页码（默认1）
        - page_size: 每页数量（默认10，最大100）
        - search: 搜索关键词（搜索试卷代码、名称）
        - min_duration: 最小时长（分钟）
        - max_duration: 最大时长（分钟）
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "count": 总数,
            "next": 下一页URL,
            "previous": 上一页URL,
            "results": [试卷列表]
        }
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 获取查询参数
        search = request.query_params.get('search')
        min_duration = request.query_params.get('min_duration')
        max_duration = request.query_params.get('max_duration')
        
        # 基础查询集
        queryset = ExamPaper.objects.all()
        
        # 搜索
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # 时长过滤
        if min_duration:
            try:
                min_duration = int(min_duration)
                queryset = queryset.filter(total_duration_min__gte=min_duration)
            except ValueError:
                pass
        
        if max_duration:
            try:
                max_duration = int(max_duration)
                queryset = queryset.filter(total_duration_min__lte=max_duration)
            except ValueError:
                pass
        
        # 分页
        paginator = ExamPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ExamPaperListSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message='查询成功'
            )
        
        # 如果不分页
        serializer = ExamPaperListSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


class ExamPaperDetailView(APIView, ResponseMixin):
    """
    考试试卷详情视图（包含所有模块）
    
    GET /api/exam/paper/detail/<id>/
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {试卷详细信息，包含modules列表}
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            paper = ExamPaper.objects.get(pk=pk)
            serializer = ExamPaperDetailSerializer(paper)
            return self.success_response(
                data=serializer.data,
                message='查询成功'
            )
        except ExamPaper.DoesNotExist:
            return self.not_found_response(
                message='试卷不存在'
            )


class ExamPaperByCodeView(APIView, ResponseMixin):
    """
    通过试卷代码查询试卷
    
    GET /api/exam/paper/code/<code>/
    
    返回试卷详细信息
    """
    permission_classes = [AllowAny]
    
    def get(self, request, code):
        try:
            paper = ExamPaper.objects.get(code=code)
            serializer = ExamPaperDetailSerializer(paper)
            return self.success_response(
                data=serializer.data,
                message='查询成功'
            )
        except ExamPaper.DoesNotExist:
            return self.not_found_response(
                message=f'试卷 {code} 不存在'
            )


class ExamPaperSearchView(APIView, ResponseMixin):
    """
    试卷搜索视图
    
    GET /api/exam/paper/search/
    Query参数:
        - q: 搜索关键词（必需）
        - page: 页码（可选）
        - page_size: 每页数量（可选）
    
    在试卷代码、名称和描述中搜索
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return self.bad_request_response(
                message='搜索关键词不能为空'
            )
        
        # 搜索
        queryset = ExamPaper.objects.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).distinct()
        
        # 分页
        paginator = ExamPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ExamPaperListSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message=f'搜索到 {queryset.count()} 条结果'
            )
        
        # 不分页
        serializer = ExamPaperListSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message=f'搜索到 {queryset.count()} 条结果'
        )


# ==================== ExamModule 视图 ====================

class ExamModuleListView(APIView, ResponseMixin):
    """
    考试模块列表视图（分页查询）
    
    GET /api/exam/module/list/
    Query参数:
        - page: 页码（默认1）
        - page_size: 每页数量（默认10，最大100）
        - is_activate: 是否激活（可选，true/false）
        - module_type: 模块类型（可选）
        - paper: 试卷ID（可选，查询指定试卷的模块）
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "count": 总数,
            "next": 下一页URL,
            "previous": 上一页URL,
            "results": [模块列表]
        }
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 获取查询参数
        is_activate = request.query_params.get('is_activate')
        module_type = request.query_params.get('module_type')
        paper = request.query_params.get('paper')
        
        # 基础查询集
        queryset = ExamModule.objects.all()
        
        # 过滤条件
        if is_activate is not None:
            is_activate_bool = is_activate.lower() == 'true'
            queryset = queryset.filter(is_activate=is_activate_bool)
        
        if module_type:
            queryset = queryset.filter(module_type=module_type)
        
        if paper:
            queryset = queryset.filter(exam_paper__id=paper)
        
        # 排序
        queryset = queryset.order_by('display_order')
        
        # 分页
        paginator = ExamPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = ExamModuleSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message='查询成功'
            )
        
        # 如果不分页
        serializer = ExamModuleSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


class ExamModuleDetailView(APIView, ResponseMixin):
    """
    考试模块详情视图
    
    GET /api/exam/module/detail/<id>/
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {模块详细信息}
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            module = ExamModule.objects.get(pk=pk)
            serializer = ExamModuleDetailSerializer(module)
            return self.success_response(
                data=serializer.data,
                message='查询成功'
            )
        except ExamModule.DoesNotExist:
            return self.not_found_response(
                message='模块不存在'
            )


class ExamPaperModulesView(APIView, ResponseMixin):
    """
    获取指定试卷的所有模块
    
    GET /api/exam/paper/<paper_id>/modules/
    Query参数:
        - is_activate: 是否只显示激活的模块（可选，默认true）
    
    返回指定试卷的所有模块列表（按显示顺序排序）
    """
    permission_classes = [AllowAny]
    
    def get(self, request, paper_id):
        try:
            paper = ExamPaper.objects.get(pk=paper_id)
        except ExamPaper.DoesNotExist:
            return self.not_found_response(
                message='试卷不存在'
            )
        
        # 获取is_activate参数
        is_activate_param = request.query_params.get('is_activate', 'true')
        is_activate = is_activate_param.lower() == 'true'
        
        # 查询模块
        if is_activate:
            modules = paper.exammodule_set.filter(is_activate=True).order_by('display_order')
        else:
            modules = paper.exammodule_set.all().order_by('display_order')
        
        # 序列化
        serializer = ExamModuleSerializer(modules, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


class ExamModuleTypesView(APIView, ResponseMixin):
    """
    获取所有模块类型
    
    GET /api/exam/module/types/
    
    返回所有可用的模块类型列表
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        types = [
            {
                'value': code,
                'label': label
            }
            for code, label in ExamModule.MODULE_TYPE
        ]
        
        return self.success_response(
            data=types,
            message='查询成功'
        )
