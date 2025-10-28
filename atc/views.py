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

# ==================== ATC Questions 视图 ====================

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
                    module_type='ATC_SIM',
                    is_activate=True
                )
            except ExamModule.DoesNotExist:
                return self.error_response(message='模块不存在或未启用')
        elif mode == 'random':
            # 随机选择一个模块
            modules = ExamModule.objects.filter(
                module_type='ATC_SIM',
                is_activate=True
            )
            
            if not modules.exists():
                return self.error_response(message='没有可用的ATC模拟通话模块')
            
            # 随机选择
            module = random.choice(list(modules))
        else:
            return self.error_response(message='请提供id参数或设置mode=random')
        
        # 获取模块的所有场景
        scenarios = module.atc_scenarios.filter(is_active=True).select_related('airport').prefetch_related(
            'atc_turns__audio'
        ).order_by('created_at')
        
        # 序列化场景和轮次数据
        scenarios_data = []
        total_turns = 0
        
        for scenario in scenarios:
            # 获取该场景的所有激活轮次
            turns = scenario.atc_turns.filter(is_active=True).order_by('turn_number')
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
            module_type='ATC_SIM',
            is_activate=True
        ).prefetch_related('atc_scenarios__airport', 'atc_scenarios__atc_turns__audio').order_by('display_order', 'id')
        
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
                turns = scenario.atc_turns.filter(is_active=True).order_by('turn_number')
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
    
    请求体（支持两种方式）：
    方式1 - 直接上传音频文件（multipart/form-data）：
    {
        "turn_id": 1,
        "answer_audio_file": <file>,  // 上传的音频文件
        "mode_type": "practice",  // practice 或 exam
        "module_id": 1,  // 可选，模块ID
        "is_timeout": false,
        "score": 85.5  // 可选
    }
    
    方式2 - 提供音频资源ID（application/json）：
    {
        "turn_id": 1,
        "audio_file_path_id": 2,  // 已存在的音频资源ID
        "mode_type": "practice",
        "module_id": 1,  // 可选
        "is_timeout": false,
        "score": 85.5  // 可选
    }
    
    返回：
    {
        "response_id": 123,
        "audio_id": 456,  // 新创建的音频资源ID（如果上传了文件）
        "message": "答题记录已保存"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        print(request.data)
        
        turn_id = request.data.get('turn_id')
        mode_type = request.data.get('mode_type', 'practice')
        module_id = request.data.get('module_id')
        is_timeout = request.data.get('is_timeout', False)
        score = request.data.get('score')
        
        # 验证参数
        if not turn_id:
            return self.error_response(message='缺少参数: turn_id')
        
        try:
            turn = AtcTurn.objects.get(id=turn_id)
        except AtcTurn.DoesNotExist:
            return self.error_response(message='轮次不存在')
        
        # 处理音频资源（支持两种方式）
        audio_file = None
        audio_id = None
        
        # 方式1：前端上传音频文件
        answer_audio_file = request.FILES.get('answer_audio_file')
        if answer_audio_file:
            from media.models import MediaAsset
            import re
            
            # 从文件名中提取时长信息（如果有）
            # 文件名格式：xxxxx.durationTime=16956.mp3 或 xxxxx.durationTime16956.mp3
            duration_ms = None
            filename = answer_audio_file.name
            duration_match = re.search(r'durationTime[=_]?(\d+)', filename)
            if duration_match:
                duration_ms = int(duration_match.group(1))
            
            # 创建音频资源
            audio_file = MediaAsset.objects.create(
                media_type='audio',
                file=answer_audio_file,
                duration_ms=duration_ms,
                description=f'ATC答题录音 - 用户{user.id} - 轮次{turn_id}'
            )
            audio_id = audio_file.id
        
        # 方式2：前端提供已存在的音频资源ID
        else:
            audio_file_path_id = request.data.get('audio_file_path_id')
            if audio_file_path_id:
                from media.models import MediaAsset
                try:
                    audio_file = MediaAsset.objects.get(id=audio_file_path_id)
                    audio_id = audio_file.id
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
        
        # 如果提供了模块ID，关联到该模块
        if module_id:
            try:
                module = ExamModule.objects.get(id=module_id)
                response.modules.add(module)
            except ExamModule.DoesNotExist:
                pass  # 模块不存在，继续处理，不影响主流程
        
        return self.success_response(
            data={
                'response_id': response.id,
                'audio_id': audio_id,
                'is_timeout': is_timeout,
                'score': float(score) if score else None
            },
            message='答题记录已保存'
        )


