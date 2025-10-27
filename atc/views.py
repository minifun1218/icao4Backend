"""
ATC 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import random

from common.response import ApiResponse
from common.mixins import ResponseMixin
from exam.models import ExamModule
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


# ==================== ATC Questions 视图（类似 MCQ）====================

class AtcQuestionsView(APIView, ResponseMixin):
    """
    获取ATC通讯题目
    
    支持两种模式：
    1. 按模块获取：GET /api/atc/questions?id=1
    2. 随机模块：GET /api/atc/questions?mode=random
    
    返回格式：
    {
        "module": {
            "id": 1,
            "title": "ATC通讯模块1",
            "scenario_count": 3
        },
        "scenarios": [
            {
                "id": 1,
                "title": "场景标题",
                "airport": {...},
                "turns": [...]
            }
        ]
    }
    
    参数：
    - id: ExamModule的ID（指定模块）
    - mode: random（随机选择一个模块）
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        module_id = request.query_params.get('id')
        mode = request.query_params.get('mode')
        
        # 新逻辑：按模块获取或随机模块
        if module_id or mode == 'random':
            return self._get_module_scenarios(request, module_id, mode)
        
        # 如果两个参数都不提供，返回错误
        return self.error_response(message='请提供id参数或设置mode=random')
    
    def _get_module_scenarios(self, request, module_id=None, mode=None):
        """获取指定模块或随机模块的所有场景和轮次"""
        user = request.user
        
        # 获取模块
        if module_id:
            # 按ID获取指定模块
            try:
                module = ExamModule.objects.get(
                    id=module_id,
                    module_type='ATC_COMM',
                    is_activate=True
                )
            except ExamModule.DoesNotExist:
                return self.error_response(message='模块不存在或未启用')
        elif mode == 'random':
            # 随机选择一个模块
            modules = ExamModule.objects.filter(
                module_type='ATC_COMM',
                is_activate=True
            )
            
            if not modules.exists():
                return self.error_response(message='没有可用的ATC通讯模块')
            
            # 随机选择
            module = random.choice(list(modules))
        else:
            return self.error_response(message='请提供id参数或设置mode=random')
        
        # 获取模块的所有场景
        scenarios = module.atc_scenarios.filter(is_active=True).select_related('airport').prefetch_related(
            'turns__audio'
        ).order_by('created_at')
        
        # 序列化场景和轮次数据
        scenarios_data = []
        total_turns = 0
        
        for scenario in scenarios:
            # 获取该场景的所有激活轮次
            turns = scenario.turns.filter(is_active=True).order_by('turn_number')
            turn_count = turns.count()
            total_turns += turn_count
            
            # 序列化轮次
            turns_data = []
            for turn in turns:
                # 序列化音频信息
                audio_info = None
                if turn.audio:
                    audio_info = {
                        'id': turn.audio.id,
                        'uri': turn.audio.uri,
                        'duration_ms': turn.audio.duration_ms
                    }
                
                # 如果用户登录，检查该轮次是否已答
                is_answered = False
                if user.is_authenticated:
                    is_answered = AtcTurnResponse.objects.filter(
                        user=user,
                        atc_turn=turn
                    ).exists()
                
                turns_data.append({
                    'id': turn.id,
                    'turn_number': turn.turn_number,
                    'speaker_type': turn.speaker_type,
                    'audio': turn.audio_id if turn.audio else None,
                    'audio_info': audio_info,
                    'is_answered': is_answered if user.is_authenticated else None
                })
            
            # 序列化机场信息
            airport_info = None
            if scenario.airport:
                airport_info = {
                    'id': scenario.airport.id,
                    'icao': scenario.airport.icao,
                    'name': scenario.airport.name,
                    'city': scenario.airport.city,
                    'country': scenario.airport.country
                }
            
            scenarios_data.append({
                'id': scenario.id,
                'title': scenario.title,
                'description': scenario.description,
                'airport': airport_info,
                'turn_count': turn_count,
                'turns': turns_data
            })
        
        return self.success_response(
            data={
                'module': {
                    'id': module.id,
                    'title': module.title or f'模块 {module.id}',
                    'display_order': module.display_order,
                    'duration': module.duration,
                    'score': module.score,
                    'scenario_count': len(scenarios_data),
                    'turn_count': total_turns
                },
                'scenarios': scenarios_data
            },
            message='查询成功'
        )


class AtcQuestionsAllView(APIView, ResponseMixin):
    """
    获取所有ATC通讯模块及用户答题情况
    
    GET /api/atc/questions/all/
    
    返回格式：
    {
        "is_authenticated": true,
        "modules": [
            {
                "id": 1,
                "title": "ATC通讯模块1",
                "turn_count": 15,
                "answered_count": 8,
                "progress": 53.3,
                "scenarios": [...]
            }
        ],
        "total_modules": 3,
        "total_turns": 45,
        "total_answered": 25,
        "overall_progress": 55.6
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = request.user
        
        # 获取所有ATC通讯类型的模块
        modules = ExamModule.objects.filter(
            module_type='ATC_COMM',
            is_activate=True
        ).prefetch_related('atc_scenarios__airport', 'atc_scenarios__turns__audio').order_by('display_order', 'id')
        
        modules_data = []
        total_turns = 0
        total_answered = 0
        
        # 检查用户是否已登录
        is_authenticated = user.is_authenticated
        
        for module in modules:
            # 获取该模块关联的所有场景
            scenarios = module.atc_scenarios.filter(is_active=True).order_by('created_at')
            
            # 统计该模块的所有轮次
            module_turn_count = 0
            module_answered_count = 0
            
            scenarios_data = []
            for scenario in scenarios:
                # 获取该场景的所有激活轮次
                turns = scenario.turns.filter(is_active=True).order_by('turn_number')
                turn_count = turns.count()
                module_turn_count += turn_count
                
                # 序列化机场信息
                airport_info = None
                if scenario.airport:
                    airport_info = {
                        'id': scenario.airport.id,
                        'icao': scenario.airport.icao,
                        'name': scenario.airport.name,
                        'city': scenario.airport.city,
                        'country': scenario.airport.country
                    }
                
                # 序列化轮次
                turns_data = []
                for turn in turns:
                    # 序列化音频信息
                    audio_info = None
                    if turn.audio:
                        audio_info = {
                            'id': turn.audio.id,
                            'uri': turn.audio.uri,
                            'duration_ms': turn.audio.duration_ms
                        }
                    
                    # 如果用户登录，检查该轮次是否已答
                    is_answered = False
                    if is_authenticated:
                        is_answered = AtcTurnResponse.objects.filter(
                            user=user,
                            atc_turn=turn
                        ).exists()
                        if is_answered:
                            module_answered_count += 1
                    
                    turns_data.append({
                        'id': turn.id,
                        'turn_number': turn.turn_number,
                        'speaker_type': turn.speaker_type,
                        'audio': turn.audio_id if turn.audio else None,
                        'audio_info': audio_info,
                        'is_answered': is_answered if is_authenticated else None
                    })
                
                scenarios_data.append({
                    'id': scenario.id,
                    'title': scenario.title,
                    'description': scenario.description,
                    'airport': airport_info,
                    'turn_count': turn_count,
                    'turns': turns_data
                })
            
            if module_turn_count == 0:
                continue
            
            # 计算进度
            progress = round((module_answered_count / module_turn_count * 100), 1) if module_turn_count > 0 else 0
            
            modules_data.append({
                'id': module.id,
                'title': module.title or f'模块 {module.id}',
                'display_order': module.display_order or 0,
                'scenario_count': len(scenarios_data),
                'turn_count': module_turn_count,
                'answered_count': module_answered_count,
                'progress': progress,
                'duration': module.duration,
                'score': module.score,
                'scenarios': scenarios_data,
                'created_at': module.created_at
            })
            
            total_turns += module_turn_count
            total_answered += module_answered_count
        
        # 计算总体进度
        overall_progress = round((total_answered / total_turns * 100), 1) if total_turns > 0 else 0
        
        return self.success_response(
            data={
                'is_authenticated': is_authenticated,
                'modules': modules_data,
                'total_modules': len(modules_data),
                'total_turns': total_turns,
                'total_answered': total_answered,
                'overall_progress': overall_progress
            },
            message='查询成功' if is_authenticated else '查询成功（未登录用户无答题记录）'
        )


class AtcSubmitAnswerView(APIView, ResponseMixin):
    """
    提交ATC通讯答题
    
    POST /api/atc/submit/
    
    请求体：
    {
        "turn_id": 1,
        "audio_file_path_id": 2,  // 必填
        "mode_type": "practice",  // practice 或 exam
        "is_timeout": false,
        "score": 85.5  // 可选
    }
    
    返回：
    {
        "response_id": 123,
        "message": "答题记录已保存"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        turn_id = request.data.get('turn_id')
        audio_file_path_id = request.data.get('audio_file_path_id')
        mode_type = request.data.get('mode_type', 'practice')
        is_timeout = request.data.get('is_timeout', False)
        score = request.data.get('score')
        
        # 验证参数
        if not turn_id:
            return self.error_response(message='缺少参数: turn_id')
        
        if not audio_file_path_id:
            return self.error_response(message='缺少参数: audio_file_path_id')
        
        try:
            turn = AtcTurn.objects.get(id=turn_id)
        except AtcTurn.DoesNotExist:
            return self.error_response(message='轮次不存在')
        
        # 获取答题音频
        from media.models import MediaAsset
        try:
            audio_file = MediaAsset.objects.get(id=audio_file_path_id)
        except MediaAsset.DoesNotExist:
            return self.error_response(message='音频资源不存在')
        
        # 创建答题记录
        response = AtcTurnResponse.objects.create(
            user=user,
            atc_turn=turn,
            audio_file_path=audio_file,
            mode_type=mode_type,
            is_timeout=is_timeout,
            score=score
        )
        
        return self.success_response(
            data={
                'response_id': response.id,
                'is_timeout': is_timeout,
                'score': float(score) if score else None
            },
            message='答题记录已保存'
        )


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
