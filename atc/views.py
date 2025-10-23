"""
ATC 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from common.response import ApiResponse
from common.mixins import ResponseMixin
from .models import Airport, AtcScenario, AtcTurn, AtcTurnResponse
from .serializers import (
    AirportSerializer,
    AirportListSerializer,
    AtcScenarioSerializer,
    AtcScenarioListSerializer,
    AtcScenarioDetailSerializer,
    AtcTurnSerializer,
    AtcTurnDetailSerializer,
    AtcTurnResponseSerializer
)


class AtcPagination(PageNumberPagination):
    """
    ATC分页类
    """
    page_size = 10  # 每页显示10条
    page_size_query_param = 'page_size'  # 允许客户端通过page_size参数自定义每页数量
    max_page_size = 100  # 最大每页100条
    page_query_param = 'page'  # 页码参数名


# ==================== Airport 视图 ====================

class AirportListView(APIView, ResponseMixin):
    """
    机场列表视图（分页查询）
    
    GET /api/atc/airport/list/
    Query参数:
        - page: 页码（默认1）
        - page_size: 每页数量（默认10，最大100）
        - is_active: 是否激活（可选，true/false）
        - country: 国家过滤（可选）
        - city: 城市过滤（可选）
        - search: 搜索关键词（搜索ICAO代码、机场名称、城市）
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "count": 总数,
            "next": 下一页URL,
            "previous": 上一页URL,
            "results": [机场列表]
        }
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 获取查询参数
        is_active = request.query_params.get('is_active')
        country = request.query_params.get('country')
        city = request.query_params.get('city')
        search = request.query_params.get('search')
        
        # 基础查询集
        queryset = Airport.objects.all()
        
        # 过滤条件
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # 搜索
        if search:
            queryset = queryset.filter(
                Q(icao__icontains=search) |
                Q(name__icontains=search) |
                Q(city__icontains=search)
            )
        
        # 分页
        paginator = AtcPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AirportListSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message='查询成功'
            )
        
        # 如果不分页
        serializer = AirportListSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


class AirportDetailView(APIView, ResponseMixin):
    """
    机场详情视图
    
    GET /api/atc/airport/detail/<id>/
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {机场详细信息}
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            airport = Airport.objects.get(pk=pk)
            serializer = AirportSerializer(airport)
            return self.success_response(
                data=serializer.data,
                message='查询成功'
            )
        except Airport.DoesNotExist:
            return self.not_found_response(
                message='机场不存在'
            )


class AirportByIcaoView(APIView, ResponseMixin):
    """
    通过ICAO代码查询机场
    
    GET /api/atc/airport/icao/<icao>/
    
    返回机场详细信息
    """
    permission_classes = [AllowAny]
    
    def get(self, request, icao):
        try:
            airport = Airport.objects.get(icao=icao.upper())
            serializer = AirportSerializer(airport)
            return self.success_response(
                data=serializer.data,
                message='查询成功'
            )
        except Airport.DoesNotExist:
            return self.not_found_response(
                message=f'机场 {icao} 不存在'
            )


# ==================== AtcScenario 视图 ====================

class AtcScenarioListView(APIView, ResponseMixin):
    """
    ATC场景列表视图（分页查询）
    
    GET /api/atc/scenario/list/
    Query参数:
        - page: 页码（默认1）
        - page_size: 每页数量（默认10，最大100）
        - is_active: 是否激活（可选，true/false）
        - airport: 机场ID（可选）
        - airport_icao: 机场ICAO代码（可选）
        - module: 模块ID（可选）
        - search: 搜索关键词（搜索标题、描述）
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "count": 总数,
            "next": 下一页URL,
            "previous": 上一页URL,
            "results": [场景列表]
        }
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 获取查询参数
        is_active = request.query_params.get('is_active')
        airport = request.query_params.get('airport')
        airport_icao = request.query_params.get('airport_icao')
        module = request.query_params.get('module')
        search = request.query_params.get('search')
        
        # 基础查询集
        queryset = AtcScenario.objects.select_related('airport', 'module').all()
        
        # 过滤条件
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        if airport:
            queryset = queryset.filter(airport_id=airport)
        
        if airport_icao:
            queryset = queryset.filter(airport__icao=airport_icao.upper())
        
        if module:
            queryset = queryset.filter(module_id=module)
        
        # 搜索
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        # 分页
        paginator = AtcPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AtcScenarioListSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message='查询成功'
            )
        
        # 如果不分页
        serializer = AtcScenarioListSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


class AtcScenarioDetailView(APIView, ResponseMixin):
    """
    ATC场景详情视图（包含所有轮次）
    
    GET /api/atc/scenario/detail/<id>/
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {场景详细信息，包含turns列表}
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            scenario = AtcScenario.objects.select_related('airport', 'module').get(pk=pk)
            serializer = AtcScenarioDetailSerializer(scenario)
            return self.success_response(
                data=serializer.data,
                message='查询成功'
            )
        except AtcScenario.DoesNotExist:
            return self.not_found_response(
                message='场景不存在'
            )


class AtcScenarioActiveListView(APIView, ResponseMixin):
    """
    获取激活的ATC场景列表
    
    GET /api/atc/scenario/active/
    Query参数:
        - airport: 机场ID（可选）
        - airport_icao: 机场ICAO代码（可选）
        - page: 页码（可选）
        - page_size: 每页数量（可选）
    
    返回所有激活的场景
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 基础查询集
        queryset = AtcScenario.objects.select_related('airport', 'module').filter(is_active=True)
        
        # 过滤条件
        airport = request.query_params.get('airport')
        airport_icao = request.query_params.get('airport_icao')
        
        if airport:
            queryset = queryset.filter(airport_id=airport)
        
        if airport_icao:
            queryset = queryset.filter(airport__icao=airport_icao.upper())
        
        # 分页（可选）
        if request.query_params.get('page'):
            paginator = AtcPagination()
            page = paginator.paginate_queryset(queryset, request)
            if page is not None:
                serializer = AtcScenarioDetailSerializer(page, many=True)
                result = paginator.get_paginated_response(serializer.data)
                return self.success_response(
                    data=result.data,
                    message='查询成功'
                )
        
        # 不分页，返回所有
        serializer = AtcScenarioDetailSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


# ==================== AtcTurn 视图 ====================

class AtcTurnListView(APIView, ResponseMixin):
    """
    ATC轮次列表视图（分页查询）
    
    GET /api/atc/turn/list/
    Query参数:
        - page: 页码（默认1）
        - page_size: 每页数量（默认10，最大100）
        - is_active: 是否激活（可选，true/false）
        - scenario: 场景ID（可选）
        - speaker_type: 说话者类型（可选，pilot/controller）
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "count": 总数,
            "next": 下一页URL,
            "previous": 上一页URL,
            "results": [轮次列表]
        }
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 获取查询参数
        is_active = request.query_params.get('is_active')
        scenario = request.query_params.get('scenario')
        speaker_type = request.query_params.get('speaker_type')
        
        # 基础查询集
        queryset = AtcTurn.objects.select_related('scenario', 'audio').all()
        
        # 过滤条件
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        if scenario:
            queryset = queryset.filter(scenario_id=scenario)
        
        if speaker_type:
            queryset = queryset.filter(speaker_type=speaker_type)
        
        # 分页
        paginator = AtcPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AtcTurnSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message='查询成功'
            )
        
        # 如果不分页
        serializer = AtcTurnSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


class AtcTurnDetailView(APIView, ResponseMixin):
    """
    ATC轮次详情视图
    
    GET /api/atc/turn/detail/<id>/
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {轮次详细信息}
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            turn = AtcTurn.objects.select_related('scenario', 'audio').get(pk=pk)
            serializer = AtcTurnDetailSerializer(turn)
            return self.success_response(
                data=serializer.data,
                message='查询成功'
            )
        except AtcTurn.DoesNotExist:
            return self.not_found_response(
                message='轮次不存在'
            )


class AtcTurnsByScenarioView(APIView, ResponseMixin):
    """
    获取指定场景的所有轮次
    
    GET /api/atc/scenario/<scenario_id>/turns/
    Query参数:
        - is_active: 是否只显示激活的轮次（可选，默认true）
    
    返回指定场景的所有轮次列表（按轮次序号排序）
    """
    permission_classes = [AllowAny]
    
    def get(self, request, scenario_id):
        try:
            scenario = AtcScenario.objects.get(pk=scenario_id)
        except AtcScenario.DoesNotExist:
            return self.not_found_response(
                message='场景不存在'
            )
        
        # 获取is_active参数
        is_active_param = request.query_params.get('is_active', 'true')
        is_active = is_active_param.lower() == 'true'
        
        # 查询轮次
        if is_active:
            turns = scenario.turns.filter(is_active=True).order_by('turn_number')
        else:
            turns = scenario.turns.all().order_by('turn_number')
        
        # 序列化
        serializer = AtcTurnSerializer(turns, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


class AtcScenarioSearchView(APIView, ResponseMixin):
    """
    ATC场景搜索视图
    
    GET /api/atc/scenario/search/
    Query参数:
        - q: 搜索关键词（必需）
        - page: 页码（可选）
        - page_size: 每页数量（可选）
    
    在场景的标题和描述中搜索
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return self.bad_request_response(
                message='搜索关键词不能为空'
            )
        
        # 搜索
        queryset = AtcScenario.objects.select_related('airport', 'module').filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(airport__name__icontains=query) |
            Q(airport__icao__icontains=query)
        ).distinct()
        
        # 分页
        paginator = AtcPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AtcScenarioListSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message=f'搜索到 {queryset.count()} 条结果'
            )
        
        # 不分页
        serializer = AtcScenarioListSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message=f'搜索到 {queryset.count()} 条结果'
        )
