"""
Vocab (航空词汇) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from common.response import ApiResponse
from common.mixins import ResponseMixin
from .models import AvVocabTopic, AvVocab, UserVocabLearning, UserTermLearning
from .serializers import (
    AvVocabTopicSerializer, 
    AvVocabSerializer,
    UserVocabLearningSerializer,
    UserTermLearningSerializer
)
from rest_framework.permissions import IsAuthenticated


class VocabPagination(PageNumberPagination):
    """Vocab分页类"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class AvVocabTopicListView(APIView, ResponseMixin):
    """航空词汇主题列表视图"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        search = request.query_params.get('search')
        
        queryset = AvVocabTopic.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name_zh__icontains=search) |
                Q(name_en__icontains=search)
            )
        
        queryset = queryset.order_by('display_order', 'id')
        
        paginator = VocabPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AvVocabTopicSerializer(page, many=True, context={'request': request})
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = AvVocabTopicSerializer(queryset, many=True, context={'request': request})
        return self.success_response(data=serializer.data, message='查询成功')


class AvVocabTopicDetailView(APIView, ResponseMixin):
    """
    航空词汇主题下的词汇列表视图
    
    GET /api/vocab/theme/<id>/ - 获取指定主题下的所有词汇
    支持分页和筛选
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            topic = AvVocabTopic.objects.get(pk=pk)
        except AvVocabTopic.DoesNotExist:
            return self.not_found_response(message='主题不存在')
        
        # 获取该主题下的所有词汇
        queryset = AvVocab.objects.filter(topic=topic).select_related('topic', 'audio_asset')
        
        # 支持搜索
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(headword__icontains=search) |
                Q(lemma__icontains=search) |
                Q(definition_zh__icontains=search)
            )
        
        # 按CEFR等级筛选
        cefr_level = request.query_params.get('cefr_level')
        if cefr_level:
            queryset = queryset.filter(cefr_level=cefr_level)
        
        queryset = queryset.order_by('-created_at')
        
        # 分页
        paginator = VocabPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AvVocabSerializer(page, many=True, context={'request': request})
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
        
        serializer = AvVocabSerializer(queryset, many=True, context={'request': request})
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


class AvVocabListView(APIView, ResponseMixin):
    """航空词汇列表视图"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        search = request.query_params.get('search')
        topic = request.query_params.get('topic')
        cefr_level = request.query_params.get('cefr_level')
        pos = request.query_params.get('pos')
        
        queryset = AvVocab.objects.select_related('topic', 'audio_asset').all()
        
        if search:
            queryset = queryset.filter(
                Q(headword__icontains=search) |
                Q(lemma__icontains=search) |
                Q(definition_zh__icontains=search)
            )
        
        if topic:
            queryset = queryset.filter(topic_id=topic)
        
        if cefr_level:
            queryset = queryset.filter(cefr_level=cefr_level)
        
        if pos:
            queryset = queryset.filter(pos=pos)
        
        queryset = queryset.order_by('-created_at')
        
        paginator = VocabPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AvVocabSerializer(page, many=True, context={'request': request})
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = AvVocabSerializer(queryset, many=True, context={'request': request})
        return self.success_response(data=serializer.data, message='查询成功')


class AvVocabDetailView(APIView, ResponseMixin):
    """航空词汇详情视图"""
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            vocab = AvVocab.objects.select_related('topic', 'audio_asset').get(pk=pk)
            serializer = AvVocabSerializer(vocab, context={'request': request})
            return self.success_response(data=serializer.data, message='查询成功')
        except AvVocab.DoesNotExist:
            return self.not_found_response(message='词汇不存在')


class AvVocabSearchView(APIView, ResponseMixin):
    """航空词汇搜索视图"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return self.bad_request_response(message='搜索关键词不能为空')
        
        queryset = AvVocab.objects.select_related('topic').filter(
            Q(headword__icontains=query) |
            Q(lemma__icontains=query) |
            Q(definition_zh__icontains=query)
        ).distinct()
        
        paginator = VocabPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AvVocabSerializer(page, many=True, context={'request': request})
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message=f'搜索到 {queryset.count()} 条结果'
            )
        
        serializer = AvVocabSerializer(queryset, many=True, context={'request': request})
        return self.success_response(
            data=serializer.data,
            message=f'搜索到 {queryset.count()} 条结果'
        )


class AvVocabStatsView(APIView, ResponseMixin):
    """
    航空词汇和术语统计视图
    
    GET /api/vocab/stats
    返回词汇和术语的总数、各主题数量、各等级数量等统计信息
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        from django.db.models import Count
        from term.models import AvTerm, AvTermsTopic
        
        # ==================== 词汇统计 ====================
        # 总词汇数
        vocab_total_count = AvVocab.objects.count()
        
        # 各主题词汇数量
        vocab_topics_stats = list(
            AvVocabTopic.objects.annotate(
                vocab_count=Count('vocabs')
            ).values(
                'id', 'code', 'name_zh', 'name_en', 'vocab_count'
            ).order_by('display_order')
        )
        
        # 各CEFR等级词汇数量
        vocab_cefr_stats = []
        for level_code, level_name in AvVocab.CERF_LEVEL:
            count = AvVocab.objects.filter(cefr_level=level_code).count()
            vocab_cefr_stats.append({
                'level': level_code,
                'level_name': level_name,
                'count': count
            })
        
        # 有音频的词汇数量
        vocab_with_audio_count = AvVocab.objects.filter(audio_asset__isnull=False).count()
        
        # 各词性统计（如果有）
        vocab_pos_stats = list(
            AvVocab.objects.exclude(pos__isnull=True).exclude(pos='')
            .values('pos')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]  # 取前10个最常见的词性
        )
        
        # ==================== 术语统计 ====================
        # 总术语数
        term_total_count = AvTerm.objects.count()
        
        # 各主题术语数量
        term_topics_stats = list(
            AvTermsTopic.objects.annotate(
                term_count=Count('terms')
            ).values(
                'id', 'code', 'name_zh', 'name_en', 'term_count'
            ).order_by('display_order')
        )
        
        # 各CEFR等级术语数量
        term_cefr_stats = []
        for level_code, level_name in AvTerm.CERF_LEVEL:
            count = AvTerm.objects.filter(cefr_level=level_code).count()
            term_cefr_stats.append({
                'level': level_code,
                'level_name': level_name,
                'count': count
            })
        
        # 有音频的术语数量
        term_with_audio_count = AvTerm.objects.filter(audio_asset__isnull=False).count()
        
        # ==================== 总体统计 ====================
        total_all_count = vocab_total_count + term_total_count
        total_with_audio_count = vocab_with_audio_count + term_with_audio_count
        
        stats_data = {
            'overall': {
                'total_count': total_all_count,
                'vocab_count': vocab_total_count,
                'term_count': term_total_count,
                'with_audio_count': total_with_audio_count,
                'audio_percentage': round((total_with_audio_count / total_all_count * 100) if total_all_count > 0 else 0, 2)
            },
            'vocabulary': {
                'overview': {
                    'total_count': vocab_total_count,
                    'with_audio_count': vocab_with_audio_count,
                    'audio_percentage': round((vocab_with_audio_count / vocab_total_count * 100) if vocab_total_count > 0 else 0, 2)
                },
                'by_topic': vocab_topics_stats,
                'by_cefr_level': vocab_cefr_stats,
                'by_pos': vocab_pos_stats
            },
            'terminology': {
                'overview': {
                    'total_count': term_total_count,
                    'with_audio_count': term_with_audio_count,
                    'audio_percentage': round((term_with_audio_count / term_total_count * 100) if term_total_count > 0 else 0, 2)
                },
                'by_topic': term_topics_stats,
                'by_cefr_level': term_cefr_stats
            }
        }
        
        return self.success_response(
            data=stats_data,
            message='获取词汇和术语统计成功'
        )


class UserVocabLearningView(APIView, ResponseMixin):
    """
    用户词汇学习记录视图
    
    POST /api/vocab/learning/vocab/ - 记录学习词汇
    GET /api/vocab/learning/vocab/ - 获取学习记录列表
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """记录或更新词汇学习"""
        vocab_id = request.data.get('vocab_id')
        mastery_level = request.data.get('mastery_level', 1)
        is_favorited = request.data.get('is_favorited', False)
        is_mastered = request.data.get('is_mastered', False)
        notes = request.data.get('notes', '')
        
        if not vocab_id:
            return self.bad_request_response(message='vocab_id不能为空')
        
        try:
            vocab = AvVocab.objects.get(id=vocab_id)
        except AvVocab.DoesNotExist:
            return self.not_found_response(message='词汇不存在')
        
        # 获取或创建学习记录
        learning, created = UserVocabLearning.objects.get_or_create(
            user=request.user,
            vocab=vocab,
            defaults={
                'mastery_level': mastery_level,
                'is_favorited': is_favorited,
                'is_mastered': is_mastered,
                'notes': notes
            }
        )
        
        if not created:
            # 更新学习记录
            learning.increment_study_count()
            if mastery_level is not None:
                learning.mastery_level = mastery_level
            if is_favorited is not None:
                learning.is_favorited = is_favorited
            if is_mastered is not None:
                learning.is_mastered = is_mastered
            if notes:
                learning.notes = notes
            learning.save()
        
        serializer = UserVocabLearningSerializer(learning)
        return self.success_response(
            data=serializer.data,
            message='学习记录已保存' if created else '学习记录已更新'
        )
    
    def get(self, request):
        """获取词汇学习记录列表"""
        user = request.user
        
        # 查询参数
        is_favorited = request.query_params.get('is_favorited')
        is_mastered = request.query_params.get('is_mastered')
        topic_id = request.query_params.get('topic')
        
        queryset = UserVocabLearning.objects.filter(user=user).select_related('vocab', 'vocab__topic')
        
        if is_favorited is not None:
            queryset = queryset.filter(is_favorited=is_favorited.lower() == 'true')
        
        if is_mastered is not None:
            queryset = queryset.filter(is_mastered=is_mastered.lower() == 'true')
        
        if topic_id:
            queryset = queryset.filter(vocab__topic_id=topic_id)
        
        # 分页
        paginator = VocabPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = UserVocabLearningSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = UserVocabLearningSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class UserTermLearningView(APIView, ResponseMixin):
    """
    用户术语学习记录视图
    
    POST /api/vocab/learning/term/ - 记录学习术语
    GET /api/vocab/learning/term/ - 获取学习记录列表
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """记录或更新术语学习"""
        from term.models import AvTerm
        
        term_id = request.data.get('term_id')
        mastery_level = request.data.get('mastery_level', 1)
        is_favorited = request.data.get('is_favorited', False)
        is_mastered = request.data.get('is_mastered', False)
        notes = request.data.get('notes', '')
        
        if not term_id:
            return self.bad_request_response(message='term_id不能为空')
        
        try:
            term = AvTerm.objects.get(id=term_id)
        except AvTerm.DoesNotExist:
            return self.not_found_response(message='术语不存在')
        
        # 获取或创建学习记录
        learning, created = UserTermLearning.objects.get_or_create(
            user=request.user,
            term=term,
            defaults={
                'mastery_level': mastery_level,
                'is_favorited': is_favorited,
                'is_mastered': is_mastered,
                'notes': notes
            }
        )
        
        if not created:
            # 更新学习记录
            learning.increment_study_count()
            if mastery_level is not None:
                learning.mastery_level = mastery_level
            if is_favorited is not None:
                learning.is_favorited = is_favorited
            if is_mastered is not None:
                learning.is_mastered = is_mastered
            if notes:
                learning.notes = notes
            learning.save()
        
        serializer = UserTermLearningSerializer(learning)
        return self.success_response(
            data=serializer.data,
            message='学习记录已保存' if created else '学习记录已更新'
        )
    
    def get(self, request):
        """获取术语学习记录列表"""
        user = request.user
        
        # 查询参数
        is_favorited = request.query_params.get('is_favorited')
        is_mastered = request.query_params.get('is_mastered')
        topic_id = request.query_params.get('topic')
        
        queryset = UserTermLearning.objects.filter(user=user).select_related('term', 'term__topic')
        
        if is_favorited is not None:
            queryset = queryset.filter(is_favorited=is_favorited.lower() == 'true')
        
        if is_mastered is not None:
            queryset = queryset.filter(is_mastered=is_mastered.lower() == 'true')
        
        if topic_id:
            queryset = queryset.filter(term__topic_id=topic_id)
        
        # 分页
        paginator = VocabPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = UserTermLearningSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = UserTermLearningSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class VocabMarkView(APIView, ResponseMixin):
    """
    词汇/术语统一标记视图（简化版接口）
    
    POST /api/vocab/mark - 标记词汇或术语
    
    请求参数:
        - vocab_id: 词汇ID（可选，与term_id二选一）
        - term_id: 术语ID（可选，与vocab_id二选一）
        - action: 操作类型（favorite/master/mastery/note）
        - mastery_level: 掌握程度（仅action=mastery时需要）
        - notes: 学习笔记（仅action=note时需要）
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """标记词汇掌握"""
        vocab_id = request.data.get('id')
        mastered = request.data.get('mastered')
        
        # 验证参数
        if not vocab_id:
            return self.bad_request_response(message='id参数不能为空')
        
        if mastered is None:
            return self.bad_request_response(message='mastered参数不能为空')
        
        try:
            vocab = AvVocab.objects.get(id=vocab_id)
        except AvVocab.DoesNotExist:
            return self.not_found_response(message='词汇不存在')
        
        # 获取或创建学习记录
        learning, created = UserVocabLearning.objects.get_or_create(
            user=request.user,
            vocab=vocab,
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
        
        serializer = UserVocabLearningSerializer(learning)
        message = '已标记为掌握' if learning.is_mastered else '已取消掌握标记'
        
        return self.success_response(data=serializer.data, message=message)


class VocabQuickActionView(APIView, ResponseMixin):
    """
    词汇快速操作视图（用于学习时快速标记）
    
    POST /api/vocab/quick-action/{vocab_id}/favorite/ - 切换收藏
    POST /api/vocab/quick-action/{vocab_id}/master/ - 切换掌握
    POST /api/vocab/quick-action/{vocab_id}/mastery/ - 更新掌握程度
    POST /api/vocab/quick-action/{vocab_id}/note/ - 添加/更新备注
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, vocab_id, action):
        """快速操作"""
        try:
            vocab = AvVocab.objects.get(id=vocab_id)
        except AvVocab.DoesNotExist:
            return self.not_found_response(message='词汇不存在')
        
        # 获取或创建学习记录
        learning, created = UserVocabLearning.objects.get_or_create(
            user=request.user,
            vocab=vocab,
            defaults={'mastery_level': 1}
        )
        
        # 如果不是新创建的记录，增加学习次数
        if not created and action != 'note':
            learning.increment_study_count()
        
        # 根据不同的操作类型处理
        if action == 'favorite':
            # 切换收藏状态
            learning.is_favorited = not learning.is_favorited
            learning.save()
            message = '已收藏' if learning.is_favorited else '已取消收藏'
            
        elif action == 'master':
            # 切换掌握状态
            learning.is_mastered = not learning.is_mastered
            # 如果标记为已掌握，自动设置掌握程度为4
            if learning.is_mastered:
                learning.mastery_level = 4
            learning.save()
            message = '已标记为掌握' if learning.is_mastered else '已取消掌握标记'
            
        elif action == 'mastery':
            # 更新掌握程度
            mastery_level = request.data.get('mastery_level')
            if mastery_level is None:
                return self.bad_request_response(message='mastery_level不能为空')
            
            try:
                mastery_level = int(mastery_level)
                if mastery_level < 0 or mastery_level > 4:
                    return self.bad_request_response(message='mastery_level必须在0-4之间')
            except ValueError:
                return self.bad_request_response(message='mastery_level必须是整数')
            
            learning.mastery_level = mastery_level
            # 如果设置为4，自动标记为已掌握
            if mastery_level == 4:
                learning.is_mastered = True
            learning.save()
            message = f'掌握程度已更新为: {learning.get_mastery_level_display()}'
            
        elif action == 'note':
            # 添加/更新备注
            notes = request.data.get('notes', '')
            learning.notes = notes
            learning.save()
            message = '备注已保存' if notes else '备注已清空'
            
        else:
            return self.bad_request_response(message=f'不支持的操作: {action}')
        
        serializer = UserVocabLearningSerializer(learning)
        return self.success_response(data=serializer.data, message=message)


class TermQuickActionView(APIView, ResponseMixin):
    """
    术语快速操作视图（用于学习时快速标记）
    
    POST /api/vocab/quick-action/term/{term_id}/favorite/ - 切换收藏
    POST /api/vocab/quick-action/term/{term_id}/master/ - 切换掌握
    POST /api/vocab/quick-action/term/{term_id}/mastery/ - 更新掌握程度
    POST /api/vocab/quick-action/term/{term_id}/note/ - 添加/更新备注
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, term_id, action):
        """快速操作"""
        from term.models import AvTerm
        
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
        
        # 如果不是新创建的记录，增加学习次数
        if not created and action != 'note':
            learning.increment_study_count()
        
        # 根据不同的操作类型处理
        if action == 'favorite':
            # 切换收藏状态
            learning.is_favorited = not learning.is_favorited
            learning.save()
            message = '已收藏' if learning.is_favorited else '已取消收藏'
            
        elif action == 'master':
            # 切换掌握状态
            learning.is_mastered = not learning.is_mastered
            # 如果标记为已掌握，自动设置掌握程度为4
            if learning.is_mastered:
                learning.mastery_level = 4
            learning.save()
            message = '已标记为掌握' if learning.is_mastered else '已取消掌握标记'
            
        elif action == 'mastery':
            # 更新掌握程度
            mastery_level = request.data.get('mastery_level')
            if mastery_level is None:
                return self.bad_request_response(message='mastery_level不能为空')
            
            try:
                mastery_level = int(mastery_level)
                if mastery_level < 0 or mastery_level > 4:
                    return self.bad_request_response(message='mastery_level必须在0-4之间')
            except ValueError:
                return self.bad_request_response(message='mastery_level必须是整数')
            
            learning.mastery_level = mastery_level
            # 如果设置为4，自动标记为已掌握
            if mastery_level == 4:
                learning.is_mastered = True
            learning.save()
            message = f'掌握程度已更新为: {learning.get_mastery_level_display()}'
            
        elif action == 'note':
            # 添加/更新备注
            notes = request.data.get('notes', '')
            learning.notes = notes
            learning.save()
            message = '备注已保存' if notes else '备注已清空'
            
        else:
            return self.bad_request_response(message=f'不支持的操作: {action}')
        
        from vocab.serializers import UserTermLearningSerializer
        serializer = UserTermLearningSerializer(learning)
        return self.success_response(data=serializer.data, message=message)


class UserLearningStatsView(APIView, ResponseMixin):
    """
    用户学习统计视图
    
    GET /api/vocab/learning/stats/ - 获取用户学习统计
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取用户学习统计"""
        user = request.user
        
        # 词汇学习统计
        vocab_total = UserVocabLearning.objects.filter(user=user).count()
        vocab_favorited = UserVocabLearning.objects.filter(user=user, is_favorited=True).count()
        vocab_mastered = UserVocabLearning.objects.filter(user=user, is_mastered=True).count()
        
        # 术语学习统计
        term_total = UserTermLearning.objects.filter(user=user).count()
        term_favorited = UserTermLearning.objects.filter(user=user, is_favorited=True).count()
        term_mastered = UserTermLearning.objects.filter(user=user, is_mastered=True).count()
        
        # 掌握程度分布（词汇）
        from django.db.models import Count
        vocab_mastery_dist = list(
            UserVocabLearning.objects.filter(user=user)
            .values('mastery_level')
            .annotate(count=Count('id'))
            .order_by('mastery_level')
        )
        
        # 掌握程度分布（术语）
        term_mastery_dist = list(
            UserTermLearning.objects.filter(user=user)
            .values('mastery_level')
            .annotate(count=Count('id'))
            .order_by('mastery_level')
        )
        
        stats_data = {
            'vocabulary': {
                'total': vocab_total,
                'favorited': vocab_favorited,
                'mastered': vocab_mastered,
                'mastery_distribution': vocab_mastery_dist
            },
            'terminology': {
                'total': term_total,
                'favorited': term_favorited,
                'mastered': term_mastered,
                'mastery_distribution': term_mastery_dist
            },
            'overall': {
                'total_learned': vocab_total + term_total,
                'total_favorited': vocab_favorited + term_favorited,
                'total_mastered': vocab_mastered + term_mastered
            }
        }
        
        return self.success_response(
            data=stats_data,
            message='获取学习统计成功'
        )