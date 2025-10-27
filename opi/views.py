"""
OPI (口语面试) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import random

from common.response import ApiResponse
from common.mixins import ResponseMixin
from exam.models import ExamModule
from .models import OpiTopic, OpiQuestion, OpiResponse
from .serializers import (
    OpiTopicSerializer,
    OpiTopicDetailSerializer,
    OpiQuestionSerializer,
    OpiResponseSerializer
)


class OpiPagination(PageNumberPagination):
    """OPI分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# ==================== OPI Questions 视图（类似 MCQ）====================

class OpiQuestionsView(APIView, ResponseMixin):
    """
    获取OPI口语面试题目
    
    支持两种模式：
    1. 按模块获取：GET /api/opi/questions?id=1
    2. 随机模块：GET /api/opi/questions?mode=random
    
    返回格式：
    {
        "module": {
            "id": 1,
            "title": "口语面试模块1",
            "question_count": 5
        },
        "topics": [
            {
                "id": 1,
                "title": "话题标题",
                "questions": [...]
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
            return self._get_module_questions(request, module_id, mode)
        
        # 如果两个参数都不提供，返回错误
        return self.error_response(message='请提供id参数或设置mode=random')
    
    def _get_module_questions(self, request, module_id=None, mode=None):
        """获取指定模块或随机模块的所有话题和题目"""
        user = request.user
        
        # 获取模块
        if module_id:
            # 按ID获取指定模块
            try:
                module = ExamModule.objects.get(
                    id=module_id,
                    module_type='SPEAKING_OPI',
                    is_activate=True
                )
            except ExamModule.DoesNotExist:
                return self.error_response(message='模块不存在或未启用')
        elif mode == 'random':
            # 随机选择一个模块
            modules = ExamModule.objects.filter(
                module_type='SPEAKING_OPI',
                is_activate=True
            )
            
            if not modules.exists():
                return self.error_response(message='没有可用的口语面试模块')
            
            # 随机选择
            module = random.choice(list(modules))
        else:
            return self.error_response(message='请提供id参数或设置mode=random')
        
        # 获取模块的所有话题
        topics = module.opi_topic.all().prefetch_related(
            'questions__prompt_audio'
        ).order_by('order')
        
        # 序列化话题和题目数据
        topics_data = []
        total_questions = 0
        
        for topic in topics:
            # 获取该话题的所有问题
            questions = topic.questions.all().order_by('QOrder')
            question_count = questions.count()
            total_questions += question_count
            
            # 序列化问题
            questions_data = []
            for question in questions:
                # 序列化音频信息
                prompt_audio_info = None
                if question.prompt_audio:
                    prompt_audio_info = {
                        'id': question.prompt_audio.id,
                        'uri': question.prompt_audio.uri,
                        'duration_ms': question.prompt_audio.duration_ms
                    }
                
                # 如果用户登录，检查该题目是否已答
                is_answered = False
                if user.is_authenticated:
                    is_answered = OpiResponse.objects.filter(
                        user=user,
                        question=question
                    ).exists()
                
                questions_data.append({
                    'id': question.id,
                    'QOrder': question.QOrder,
                    'prompt_audio': question.prompt_audio_id,
                    'prompt_audio_info': prompt_audio_info,
                    'is_answered': is_answered if user.is_authenticated else None
                })
            
            topics_data.append({
                'id': topic.id,
                'title': topic.title,
                'description': topic.description,
                'order': topic.order,
                'question_count': question_count,
                'questions': questions_data
            })
        
        return self.success_response(
            data={
                'module': {
                    'id': module.id,
                    'title': module.title or f'模块 {module.id}',
                    'display_order': module.display_order,
                    'duration': module.duration,
                    'score': module.score,
                    'topic_count': len(topics_data),
                    'question_count': total_questions
                },
                'topics': topics_data
            },
            message='查询成功'
        )


class OpiQuestionsAllView(APIView, ResponseMixin):
    """
    获取所有口语面试模块及用户答题情况
    
    GET /api/opi/questions/all/
    
    返回格式：
    {
        "is_authenticated": true,
        "modules": [
            {
                "id": 1,
                "title": "口语面试模块1",
                "question_count": 5,
                "answered_count": 2,
                "progress": 40.0,
                "topics": [...]
            }
        ],
        "total_modules": 3,
        "total_questions": 15,
        "total_answered": 8,
        "overall_progress": 53.3
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = request.user
        
        # 获取所有口语面试类型的模块
        modules = ExamModule.objects.filter(
            module_type='SPEAKING_OPI',
            is_activate=True
        ).prefetch_related('opi_topic__questions__prompt_audio').order_by('display_order', 'id')
        
        modules_data = []
        total_questions = 0
        total_answered = 0
        
        # 检查用户是否已登录
        is_authenticated = user.is_authenticated
        
        for module in modules:
            # 获取该模块关联的所有话题
            topics = module.opi_topic.all().order_by('order')
            
            # 统计该模块的所有问题
            module_question_count = 0
            module_answered_count = 0
            
            topics_data = []
            for topic in topics:
                # 获取该话题的所有问题
                questions = topic.questions.all().order_by('QOrder')
                question_count = questions.count()
                module_question_count += question_count
                
                # 序列化问题
                questions_data = []
                for question in questions:
                    # 序列化音频信息
                    prompt_audio_info = None
                    if question.prompt_audio:
                        prompt_audio_info = {
                            'id': question.prompt_audio.id,
                            'uri': question.prompt_audio.uri,
                            'duration_ms': question.prompt_audio.duration_ms
                        }
                    
                    # 如果用户登录，检查该题目是否已答
                    is_answered = False
                    if is_authenticated:
                        is_answered = OpiResponse.objects.filter(
                            user=user,
                            question=question
                        ).exists()
                        if is_answered:
                            module_answered_count += 1
                    
                    questions_data.append({
                        'id': question.id,
                        'QOrder': question.QOrder,
                        'prompt_audio': question.prompt_audio_id,
                        'prompt_audio_info': prompt_audio_info,
                        'is_answered': is_answered if is_authenticated else None
                    })
                
                topics_data.append({
                    'id': topic.id,
                    'title': topic.title,
                    'description': topic.description,
                    'order': topic.order,
                    'question_count': question_count,
                    'questions': questions_data
                })
            
            if module_question_count == 0:
                continue
            
            # 计算进度
            progress = round((module_answered_count / module_question_count * 100), 1) if module_question_count > 0 else 0
            
            modules_data.append({
                'id': module.id,
                'title': module.title or f'模块 {module.id}',
                'display_order': module.display_order or 0,
                'topic_count': len(topics_data),
                'question_count': module_question_count,
                'answered_count': module_answered_count,
                'progress': progress,
                'duration': module.duration,
                'score': module.score,
                'topics': topics_data,
                'created_at': module.created_at
            })
            
            total_questions += module_question_count
            total_answered += module_answered_count
        
        # 计算总体进度
        overall_progress = round((total_answered / total_questions * 100), 1) if total_questions > 0 else 0
        
        return self.success_response(
            data={
                'is_authenticated': is_authenticated,
                'modules': modules_data,
                'total_modules': len(modules_data),
                'total_questions': total_questions,
                'total_answered': total_answered,
                'overall_progress': overall_progress
            },
            message='查询成功' if is_authenticated else '查询成功（未登录用户无答题记录）'
        )


class OpiSubmitAnswerView(APIView, ResponseMixin):
    """
    提交OPI口语面试答题
    
    POST /api/opi/submit/
    
    请求体：
    {
        "question_id": 1,
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
        question_id = request.data.get('question_id')
        answer_audio_id = request.data.get('answer_audio_id')
        mode_type = request.data.get('mode_type', 'practice')
        is_timeout = request.data.get('is_timeout', False)
        score = request.data.get('score')
        
        # 验证参数
        if not question_id:
            return self.error_response(message='缺少参数: question_id')
        
        try:
            question = OpiQuestion.objects.get(id=question_id)
        except OpiQuestion.DoesNotExist:
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
        response = OpiResponse.objects.create(
            user=user,
            question=question,
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


class OpiTopicListView(APIView, ResponseMixin):
    """OPI话题列表视图"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        search = request.query_params.get('search')
        
        queryset = OpiTopic.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        queryset = queryset.order_by('order', '-created_at')
        
        paginator = OpiPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = OpiTopicSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = OpiTopicSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class OpiTopicDetailView(APIView, ResponseMixin):
    """OPI话题详情视图"""
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            topic = OpiTopic.objects.get(pk=pk)
            serializer = OpiTopicDetailSerializer(topic)
            return self.success_response(data=serializer.data, message='查询成功')
        except OpiTopic.DoesNotExist:
            return self.not_found_response(message='话题不存在')


class OpiQuestionListView(APIView, ResponseMixin):
    """OPI问题列表视图"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        topic = request.query_params.get('topic')
        
        queryset = OpiQuestion.objects.select_related('topic').all()
        
        if topic:
            queryset = queryset.filter(topic_id=topic)
        
        queryset = queryset.order_by('topic', 'QOrder')
        
        paginator = OpiPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = OpiQuestionSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = OpiQuestionSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class OpiResponseListView(APIView, ResponseMixin):
    """OPI回答列表视图"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.query_params.get('user')
        question = request.query_params.get('question')
        is_timeout = request.query_params.get('is_timeout')
        
        queryset = OpiResponse.objects.select_related('question__topic', 'user').all()
        
        if user:
            queryset = queryset.filter(user_id=user)
        
        if question:
            queryset = queryset.filter(question_id=question)
        
        if is_timeout is not None:
            is_timeout_bool = is_timeout.lower() == 'true'
            queryset = queryset.filter(is_timeout=is_timeout_bool)
        
        queryset = queryset.order_by('-created_at')
        
        paginator = OpiPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = OpiResponseSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = OpiResponseSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')
