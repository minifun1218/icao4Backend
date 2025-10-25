"""
Story (故事复述) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count, Q

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
