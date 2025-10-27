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
            
            # 如果用户登录，检查该题目是否已答
            is_answered = False
            if user.is_authenticated:
                is_answered = RetellResponse.objects.filter(
                    user=user,
                    retell_item=item
                ).exists()
            
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
            item_count = items.count()
            
            if item_count == 0:
                continue
            
            # 只有登录用户才查询答题记录
            answered_count = 0
            
            if is_authenticated:
                # 统计该用户已答的题目数（去重）
                answered_item_ids = RetellResponse.objects.filter(
                    user=user,
                    retell_item__in=items
                ).values_list('retell_item_id', flat=True).distinct()
                answered_count = len(answered_item_ids)
            
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
                
                # 如果用户登录，检查该题目是否已答
                is_answered = False
                if is_authenticated:
                    is_answered = RetellResponse.objects.filter(
                        user=user,
                        retell_item=item
                    ).exists()
                
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
    
    请求体：
    {
        "item_id": 1,
        "answer_audio_id": 2,  // 可选
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
        item_id = request.data.get('item_id')
        answer_audio_id = request.data.get('answer_audio_id')
        mode_type = request.data.get('mode_type', 'practice')
        is_timeout = request.data.get('is_timeout', False)
        score = request.data.get('score')
        
        # 验证参数
        if not item_id:
            return self.error_response(message='缺少参数: item_id')
        
        try:
            item = RetellItem.objects.get(id=item_id)
        except RetellItem.DoesNotExist:
            return self.error_response(message='题目不存在')
        
        # 获取答题音频（如果提供）
        answer_audio = None
        if answer_audio_id:
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
        
        return self.success_response(
            data={
                'response_id': response.id,
                'is_timeout': is_timeout,
                'score': float(score) if score else None
            },
            message='答题记录已保存'
        )


class RetellItemListView(APIView, ResponseMixin):
    """复述题目列表视图"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        search = request.query_params.get('search')
        
        queryset = RetellItem.objects.all()
        
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        queryset = queryset.order_by('-created_at')
        
        paginator = StoryPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = RetellItemSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = RetellItemSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class RetellItemDetailView(APIView, ResponseMixin):
    """复述题目详情视图"""
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            item = RetellItem.objects.get(pk=pk)
            serializer = RetellItemSerializer(item)
            return self.success_response(data=serializer.data, message='查询成功')
        except RetellItem.DoesNotExist:
            return self.not_found_response(message='题目不存在')


class RetellResponseListView(APIView, ResponseMixin):
    """复述回答列表视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.query_params.get('user')
        item = request.query_params.get('item')
        is_timeout = request.query_params.get('is_timeout')
        
        queryset = RetellResponse.objects.select_related('retell_item', 'user').all()
        
        if user:
            queryset = queryset.filter(user_id=user)
        
        if item:
            queryset = queryset.filter(retell_item_id=item)
        
        if is_timeout is not None:
            is_timeout_bool = is_timeout.lower() == 'true'
            queryset = queryset.filter(is_timeout=is_timeout_bool)
        
        queryset = queryset.order_by('-created_at')
        
        paginator = StoryPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = RetellResponseSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = RetellResponseSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class RetellModulesListView(APIView, ResponseMixin):
    """
    以ExamModule为单位获取故事复述模块列表
    返回所有类型为 STORY_RETELL 的模块及其包含的题目
    如果用户登录，返回训练模式（practice）的答题统计
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
        
        for module in modules:
            # 获取该模块关联的所有题目
            items = module.retell_items.all().order_by('id')
            total_items = items.count()
            
            # 初始化统计数据
            answered_count = 0
            
            # 如果用户已登录，统计训练模式的答题情况
            if user.is_authenticated:
                # 统计该用户在训练模式下已答的题目数（去重）
                answered_item_ids = RetellResponse.objects.filter(
                    user=user,
                    retell_item__in=items,
                    mode_type='practice'
                ).values_list('retell_item_id', flat=True).distinct()
                answered_count = len(answered_item_ids)
            
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
                
                # 如果用户登录，检查该题目是否已答
                is_answered = False
                if user.is_authenticated:
                    is_answered = RetellResponse.objects.filter(
                        user=user,
                        retell_item=item,
                        mode_type='practice'
                    ).exists()
                
                items_data.append({
                    'id': item.id,
                    'title': item.title,
                    'audio_asset': item.audio_asset_id,
                    'audio_info': audio_info,
                    'created_at': item.created_at,
                    'is_answered': is_answered if user.is_authenticated else None
                })
            
            # 构建模块数据
            module_data = {
                'module_id': module.id,
                'module_title': module.title,
                'module_type': module.module_type,
                'display_order': module.display_order or 0,
                'duration': module.duration,
                'score': module.score,
                'total_items': total_items,
                'answered_count': answered_count if user.is_authenticated else None,
                'items': items_data,
                'created_at': module.created_at
            }
            
            modules_data.append(module_data)
        
        return self.success_response(
            data={
                'total_modules': len(modules_data),
                'modules': modules_data
            },
            message='查询成功'
        )
