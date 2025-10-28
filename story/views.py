"""
Story (故事复述) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q
import random

from common.response import ApiResponse
from common.mixins import ResponseMixin
from exam.models import ExamModule
from .models import RetellItem, RetellResponse
from .serializers import RetellItemSerializer, RetellResponseSerializer

class StoryPagination(PageNumberPagination):
    """Story分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# ==================== RetellItem 视图 ====================

class RetellQuestionsView(APIView, ResponseMixin):
    """
    获取Story复述题目
    
    支持两种模式：
    1. 按模块获取：GET /api/story/questions?id=1
    2. 随机模块：GET /api/story/questions?mode=random
    
    返回格式：
    {
        "module": {
            "id": 1,
            "title": "故事复述模块1",
            "item_count": 5
        },
        "items": [
            {
                "id": 1,
                "title": "题目标题",
                "audio_info": {...}
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
            return self._get_module_items(request, module_id, mode)
        
        # 如果两个参数都不提供，返回错误
        return self.error_response(message='请提供id参数或设置mode=random')
    
    def _get_module_items(self, request, module_id=None, mode=None):
        """获取指定模块或随机模块的所有题目"""
        user = request.user
        
        # 获取模块
        if module_id:
            # 按ID获取指定模块
            try:
                module = ExamModule.objects.get(
                    id=module_id,
                    module_type='STORY_RETELL',
                    is_activate=True
                )
            except ExamModule.DoesNotExist:
                return self.error_response(message='模块不存在或未启用')
        elif mode == 'random':
            # 随机选择一个模块
            modules = ExamModule.objects.filter(
                module_type='STORY_RETELL',
                is_activate=True
            )
            
            if not modules.exists():
                return self.error_response(message='没有可用的故事复述模块')
            
            # 随机选择
            module = random.choice(list(modules))
        else:
            return self.error_response(message='请提供id参数或设置mode=random')
        
        # 获取模块的所有题目
        items = module.retell_items.all().order_by('id')
        item_ids = list(items.values_list('id', flat=True))
        
        # 如果用户登录，获取已答题目集合（按题目分组取最近一次）
        answered_items_set = set()
        if user.is_authenticated and item_ids:
            for item_id in item_ids:
                # 获取该题目在当前模块的最近一次答题记录
                latest_response = RetellResponse.objects.filter(
                    user=user,
                    modules=module,
                    retell_item_id=item_id
                ).order_by('-created_at').first()
                
                if latest_response:
                    answered_items_set.add(item_id)
        
        # 序列化题目数据
        items_data = []
        for item in items:
            audio_info = None
            if item.audio_asset:
                audio_info = {
                    'id': item.audio_asset.id,
                    'uri': item.audio_asset.uri,
                    'duration_ms': item.audio_asset.duration_ms
                }
            
            # 如果用户登录，检查该题目是否已答（基于最新记录）
            is_answered = False
            if user.is_authenticated:
                is_answered = item.id in answered_items_set
            
            items_data.append({
                'id': item.id,
                'title': item.title,
                'audio_asset': item.audio_asset_id,
                'audio_info': audio_info,
                'created_at': item.created_at,
                'is_answered': is_answered if user.is_authenticated else None
            })
        
        return self.success_response(
            data={
                'module': {
                    'id': module.id,
                    'title': module.title or f'模块 {module.id}',
                    'display_order': module.display_order,
                    'duration': module.duration,
                    'score': module.score,
                    'item_count': len(items_data)
                },
                'items': items_data
            },
            message='查询成功'
        )


class RetellQuestionsAllView(APIView, ResponseMixin):
    """
    获取所有故事复述模块及用户答题情况
    
    GET /api/story/questions/all/
    
    返回格式：
    {
        "is_authenticated": true,
        "modules": [
            {
                "id": 1,
                "title": "故事复述模块1",
                "item_count": 5,
                "answered_count": 2,
                "progress": 40.0,
                "duration": 600000,
                "score": 100,
                "items": [...]
            }
        ],
        "total_modules": 3,
        "total_items": 15,
        "total_answered": 8,
        "overall_progress": 53.3
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = request.user
        
        # 获取所有故事复述类型的模块
        modules = ExamModule.objects.filter(
            module_type='STORY_RETELL',
            is_activate=True
        ).prefetch_related('retell_items__audio_asset').order_by('display_order', 'id')
        
        modules_data = []
        total_items = 0
        total_answered = 0
        
        # 检查用户是否已登录
        is_authenticated = user.is_authenticated
        
        for module in modules:
            # 获取该模块关联的所有题目
            items = module.retell_items.all().order_by('id')
            item_ids = list(items.values_list('id', flat=True))
            item_count = items.count()
            
            if item_count == 0:
                continue
            
            # 只有登录用户才查询答题记录（按题目分组取最近一次）
            answered_count = 0
            
            if is_authenticated and item_count > 0:
                # 按题目分组，获取每道题的最近一次答题记录
                answered_items_set = set()
                
                for item_id in item_ids:
                    # 获取该题目的最近一次答题记录
                    latest_response = RetellResponse.objects.filter(
                        user=user,
                        modules=module,
                        retell_item_id=item_id
                    ).order_by('-created_at').first()
                    
                    if latest_response:
                        answered_items_set.add(item_id)
                
                answered_count = len(answered_items_set)
            
            # 计算进度
            progress = round((answered_count / item_count * 100), 1) if item_count > 0 else 0
            
            # 序列化题目数据
            items_data = []
            for item in items:
                audio_info = None
                if item.audio_asset:
                    audio_info = {
                        'id': item.audio_asset.id,
                        'uri': item.audio_asset.uri,
                        'duration_ms': item.audio_asset.duration_ms
                    }
                
                # 如果用户登录，检查该题目是否已答（基于最新记录）
                is_answered = False
                if is_authenticated:
                    is_answered = item.id in answered_items_set
                
                items_data.append({
                    'id': item.id,
                    'title': item.title,
                    'audio_asset': item.audio_asset_id,
                    'audio_info': audio_info,
                    'created_at': item.created_at,
                    'is_answered': is_answered if is_authenticated else None
                })
            
            modules_data.append({
                'id': module.id,
                'title': module.title or f'模块 {module.id}',
                'display_order': module.display_order or 0,
                'item_count': item_count,
                'answered_count': answered_count,
                'progress': progress,
                'duration': module.duration,
                'score': module.score,
                'items': items_data,
                'created_at': module.created_at
            })
            
            total_items += item_count
            total_answered += answered_count
        
        # 计算总体进度
        overall_progress = round((total_answered / total_items * 100), 1) if total_items > 0 else 0
        
        return self.success_response(
            data={
                'is_authenticated': is_authenticated,
                'modules': modules_data,
                'total_modules': len(modules_data),
                'total_items': total_items,
                'total_answered': total_answered,
                'overall_progress': overall_progress
            },
            message='查询成功' if is_authenticated else '查询成功（未登录用户无答题记录）'
        )


class RetellSubmitAnswerView(APIView, ResponseMixin):
    """
    提交故事复述答题
    
    POST /api/story/submit/
    
    请求体（支持两种方式）：
    方式1 - 上传音频文件（multipart/form-data）：
    {
        "item_id": 1,
        "answer_audio_file": <文件对象>,  // 音频文件
        "mode_type": "practice",  // practice 或 exam
        "is_timeout": false,
        "score": 85.5,  // 可选
        "module_id": 1  // 可选：指定所属模块ID
    }
    
    方式2 - 使用已存在的音频ID（application/json）：
    {
        "item_id": 1,
        "answer_audio_id": 2,  // 已存在的音频资源ID
        "mode_type": "practice",
        "is_timeout": false,
        "score": 85.5,
        "module_id": 1
    }
    
    返回：
    {
        "response_id": 123,
        "audio_id": 456,
        "message": "答题记录已保存"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        item_id = request.data.get('item_id')
        answer_audio_id = request.data.get('answer_audio_id')
        answer_audio_file = request.FILES.get('answer_audio_file')
        mode_type = request.data.get('mode_type', 'practice')
        module_id = request.data.get('module_id')
        
        # 处理 is_timeout 参数（兼容字符串格式）
        is_timeout_raw = request.data.get('is_timeout', False)
        if isinstance(is_timeout_raw, str):
            is_timeout = is_timeout_raw.lower() in ['true', '1', 'yes']
        else:
            is_timeout = bool(is_timeout_raw)
        
        # 处理 score 参数
        score_raw = request.data.get('score')
        score = None
        if score_raw:
            try:
                score = float(score_raw)
            except (ValueError, TypeError):
                score = None

        # 验证参数
        if not item_id:
            return self.error_response(message='缺少参数: item_id')
        
        try:
            item = RetellItem.objects.get(id=item_id)
        except RetellItem.DoesNotExist:
            return self.error_response(message='题目不存在')
        
        # 处理答题音频
        answer_audio = None
        
        # 方式1：上传新音频文件
        if answer_audio_file:
            from media.models import MediaAsset
            try:
                # 创建新的 MediaAsset 记录
                answer_audio = MediaAsset.objects.create(
                    media_type='audio',
                    file=answer_audio_file,
                    description=f'故事复述答题音频 - 用户{user.id} - 题目{item_id}'
                )
            except Exception as e:
                return self.error_response(message=f'音频文件保存失败: {str(e)}')
        
        # 方式2：使用已存在的音频ID
        elif answer_audio_id:
            from media.models import MediaAsset
            try:
                answer_audio = MediaAsset.objects.get(id=answer_audio_id)
            except MediaAsset.DoesNotExist:
                return self.error_response(message='音频资源不存在')
        
        # 创建答题记录
        response = RetellResponse.objects.create(
            user=user,
            retell_item=item,
            answer_audio=answer_audio,
            mode_type=mode_type,
            is_timeout=is_timeout,
            score=score
        )
        # 关联模块（如果提供了 module_id）
        if module_id:
            try:
                module = ExamModule.objects.get(
                    id=module_id,
                    module_type='STORY_RETELL',
                    is_activate=True
                )
                response.modules.add(module)
            except ExamModule.DoesNotExist:
                pass  # 模块不存在时忽略，不影响答题记录的保存
        else:
            # 如果没有提供 module_id，自动关联题目所属的所有模块
            item_modules = item.exam_modules.filter(is_activate=True)
            if item_modules.exists():
                response.modules.add(*item_modules)
        
        return self.success_response(
            data={
                'response_id': response.id,
                'audio_id': answer_audio.id if answer_audio else None,
                'is_timeout': is_timeout,
            },
            message='答题记录已保存'
        )

