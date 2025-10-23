"""
Term (航空术语) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from common.response import ApiResponse
from common.mixins import ResponseMixin
from .models import AvTermsTopic, AvTerm
from .serializers import AvTermsTopicSerializer, AvTermSerializer


class TermPagination(PageNumberPagination):
    """Term分页类"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AvTermsTopicListView(APIView, ResponseMixin):
    """航空术语主题列表视图"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        search = request.query_params.get('search')
        
        queryset = AvTermsTopic.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name_zh__icontains=search) |
                Q(name_en__icontains=search)
            )
        
        queryset = queryset.order_by('display_order', 'id')
        
        paginator = TermPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AvTermsTopicSerializer(page, many=True, context={'request': request})
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = AvTermsTopicSerializer(queryset, many=True, context={'request': request})
        return self.success_response(data=serializer.data, message='查询成功')


class AvTermsTopicDetailView(APIView, ResponseMixin):
    """
    航空术语主题下的术语列表视图
    
    GET /api/term/theme/<id>/ - 获取指定主题下的所有术语
    支持分页和筛选
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            topic = AvTermsTopic.objects.get(pk=pk)
        except AvTermsTopic.DoesNotExist:
            return self.not_found_response(message='主题不存在')
        
        # 获取该主题下的所有术语
        queryset = AvTerm.objects.filter(topic=topic).select_related('topic', 'audio_asset')
        
        # 支持搜索
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(headword__icontains=search) |
                Q(definition_zh__icontains=search) |
                Q(definition_en__icontains=search)
            )
        
        # 按CEFR等级筛选
        cefr_level = request.query_params.get('cefr_level')
        if cefr_level:
            queryset = queryset.filter(cefr_level=cefr_level)
        
        queryset = queryset.order_by('-created_at')
        
        # 分页
        paginator = TermPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AvTermSerializer(page, many=True, context={'request': request})
            result = paginator.get_paginated_response(serializer.data)
            
            # 添加主题信息
            response_data = result.data
            response_data['topic'] = {
                'id': topic.id,
                'code': topic.code,
                'name_zh': topic.name_zh,
                'name_en': topic.name_en,
                'description': topic.description
            }
            
            return self.success_response(data=response_data, message='查询成功')
        
        serializer = AvTermSerializer(queryset, many=True, context={'request': request})
        return self.success_response(
            data={
                'topic': {
                    'id': topic.id,
                    'code': topic.code,
                    'name_zh': topic.name_zh,
                    'name_en': topic.name_en,
                    'description': topic.description
                },
                'results': serializer.data
            },
            message='查询成功'
        )


class AvTermListView(APIView, ResponseMixin):
    """航空术语列表视图"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        search = request.query_params.get('search')
        topic = request.query_params.get('topic')
        cefr_level = request.query_params.get('cefr_level')
        
        queryset = AvTerm.objects.select_related('topic', 'audio_asset').all()
        
        if search:
            queryset = queryset.filter(
                Q(headword__icontains=search) |
                Q(definition_zh__icontains=search) |
                Q(definition_en__icontains=search)
            )
        
        if topic:
            queryset = queryset.filter(topic_id=topic)
        
        if cefr_level:
            queryset = queryset.filter(cefr_level=cefr_level)
        
        queryset = queryset.order_by('-created_at')
        
        paginator = TermPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AvTermSerializer(page, many=True, context={'request': request})
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = AvTermSerializer(queryset, many=True, context={'request': request})
        return self.success_response(data=serializer.data, message='查询成功')


class AvTermDetailView(APIView, ResponseMixin):
    """航空术语详情视图"""
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            term = AvTerm.objects.select_related('topic', 'audio_asset').get(pk=pk)
            serializer = AvTermSerializer(term, context={'request': request})
            return self.success_response(data=serializer.data, message='查询成功')
        except AvTerm.DoesNotExist:
            return self.not_found_response(message='术语不存在')


class AvTermSearchView(APIView, ResponseMixin):
    """航空术语搜索视图"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return self.bad_request_response(message='搜索关键词不能为空')
        
        queryset = AvTerm.objects.select_related('topic').filter(
            Q(headword__icontains=query) |
            Q(definition_zh__icontains=query) |
            Q(definition_en__icontains=query)
        ).distinct()
        
        paginator = TermPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AvTermSerializer(page, many=True, context={'request': request})
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message=f'搜索到 {queryset.count()} 条结果'
            )
        
        serializer = AvTermSerializer(queryset, many=True, context={'request': request})
        return self.success_response(
            data=serializer.data,
            message=f'搜索到 {queryset.count()} 条结果'
        )


class AvTermStatsView(APIView, ResponseMixin):
    """
    航空术语统计视图
    
    GET /api/term/stats
    返回术语的总数、各主题数量、各等级数量等统计信息
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        from django.db.models import Count
        
        # 总术语数
        total_count = AvTerm.objects.count()
        
        # 各主题术语数量
        topics_stats = list(
            AvTermsTopic.objects.annotate(
                term_count=Count('terms')
            ).values(
                'id', 'code', 'name_zh', 'name_en', 'term_count'
            ).order_by('display_order')
        )
        
        # 各CEFR等级术语数量
        cefr_stats = []
        for level_code, level_name in AvTerm.CERF_LEVEL:
            count = AvTerm.objects.filter(cefr_level=level_code).count()
            cefr_stats.append({
                'level': level_code,
                'level_name': level_name,
                'count': count
            })
        
        # 有音频的术语数量
        with_audio_count = AvTerm.objects.filter(audio_asset__isnull=False).count()
        
        stats_data = {
            'overview': {
                'total_count': total_count,
                'with_audio_count': with_audio_count,
                'audio_percentage': round((with_audio_count / total_count * 100) if total_count > 0 else 0, 2)
            },
            'by_topic': topics_stats,
            'by_cefr_level': cefr_stats
        }
        
        return self.success_response(
            data=stats_data,
            message='获取术语统计成功'
        )


class TermMarkView(APIView, ResponseMixin):
    """
    术语标记掌握接口
    
    POST /api/term/mark - 标记术语掌握状态
    
    请求参数:
        - id: 术语ID
        - mastered: 是否掌握（true/false）
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """标记术语掌握"""
        from vocab.models import UserTermLearning
        from vocab.serializers import UserTermLearningSerializer
        
        term_id = request.data.get('id')
        mastered = request.data.get('mastered')
        
        # 验证参数
        if not term_id:
            return self.bad_request_response(message='id参数不能为空')
        
        if mastered is None:
            return self.bad_request_response(message='mastered参数不能为空')
        
        try:
            term = AvTerm.objects.get(id=term_id)
        except AvTerm.DoesNotExist:
            return self.not_found_response(message='术语不存在')
        
        # 获取或创建学习记录
        learning, created = UserTermLearning.objects.get_or_create(
            user=request.user,
            term=term,
            defaults={'mastery_level': 1}
        )
        
        # 增加学习次数
        if not created:
            learning.increment_study_count()
        
        # 设置掌握状态
        learning.is_mastered = bool(mastered)
        if learning.is_mastered:
            learning.mastery_level = 4  # 掌握时自动设为完全掌握
        else:
            learning.mastery_level = 0  # 取消掌握时重置为未掌握
        
        learning.save()
        
        serializer = UserTermLearningSerializer(learning)
        message = '已标记为掌握' if learning.is_mastered else '已取消掌握标记'
        
        return self.success_response(data=serializer.data, message=message)
