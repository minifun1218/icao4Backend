"""
LSA (听力简答) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import random

from common.response import ApiResponse
from common.mixins import ResponseMixin
from exam.models import ExamModule
from .models import LsaDialog, LsaQuestion, LsaResponse
from .serializers import (
    LsaDialogSerializer,
    LsaDialogDetailSerializer,
    LsaQuestionSerializer,
    LsaResponseSerializer
)


class LsaPagination(PageNumberPagination):
    """LSA分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'


# ==================== LSA Questions 视图（类似 MCQ）====================

class LsaQuestionsView(APIView, ResponseMixin):
    """
    获取LSA听力简答题目
    
    支持两种模式：
    1. 按模块获取：GET /api/lsa/questions?id=1
    2. 随机模块：GET /api/lsa/questions?mode=random
    
    返回格式：
    {
        "module": {
            "id": 1,
            "title": "听力简答模块1",
            "question_count": 10
        },
        "dialogs": [
            {
                "id": 1,
                "title": "对话标题",
                "audio_info": {...},
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
        """获取指定模块或随机模块的所有对话和题目"""
        user = request.user
        
        # 获取模块
        if module_id:
            # 按ID获取指定模块
            try:
                module = ExamModule.objects.get(
                    id=module_id,
                    module_type='LISTENING_SA',
                    is_activate=True
                )
            except ExamModule.DoesNotExist:
                return self.error_response(message='模块不存在或未启用')
        elif mode == 'random':
            # 随机选择一个模块
            modules = ExamModule.objects.filter(
                module_type='LISTENING_SA',
                is_activate=True
            )
            
            if not modules.exists():
                return self.error_response(message='没有可用的听力简答模块')
            
            # 随机选择
            module = random.choice(list(modules))
        else:
            return self.error_response(message='请提供id参数或设置mode=random')
        
        # 获取模块的所有对话
        dialogs = module.module_lsa.filter(is_active=True).prefetch_related(
            'questions'
        ).order_by('display_order')
        
        # 序列化对话和题目数据
        dialogs_data = []
        total_questions = 0
        
        for dialog in dialogs:
            # 获取该对话的所有激活问题
            questions = dialog.questions.filter(is_active=True).order_by('display_order')
            question_count = questions.count()
            total_questions += question_count
            
            # 序列化音频信息
            audio_info = None
            if dialog.audio_asset:
                audio_info = {
                    'id': dialog.audio_asset.id,
                    'uri': dialog.audio_asset.uri,
                    'duration_ms': dialog.audio_asset.duration_ms
                }
            
            # 序列化问题
            questions_data = []
            for question in questions:
                # 如果用户登录，检查该题目是否已答
                is_answered = False
                if user.is_authenticated:
                    is_answered = LsaResponse.objects.filter(
                        user=user,
                        question=question
                    ).exists()
                
                questions_data.append({
                    'id': question.id,
                    'question_type': question.question_type,
                    'question_text': question.question_text,
                    'option_a': question.option_a,
                    'option_b': question.option_b,
                    'option_c': question.option_c,
                    'option_d': question.option_d,
                    'display_order': question.display_order,
                    'is_answered': is_answered if user.is_authenticated else None
                })
            
            dialogs_data.append({
                'id': dialog.id,
                'title': dialog.title,
                'description': dialog.description,
                'audio_asset': dialog.audio_asset_id if dialog.audio_asset else None,
                'audio_info': audio_info,
                'display_order': dialog.display_order,
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
                    'dialog_count': len(dialogs_data),
                    'question_count': total_questions
                },
                'dialogs': dialogs_data
            },
            message='查询成功'
        )


class LsaQuestionsAllView(APIView, ResponseMixin):
    """
    获取所有听力简答模块及用户答题情况
    
    GET /api/lsa/questions/all/
    
    返回格式：
    {
        "is_authenticated": true,
        "modules": [
            {
                "id": 1,
                "title": "听力简答模块1",
                "question_count": 10,
                "answered_count": 5,
                "progress": 50.0,
                "dialogs": [...]
            }
        ],
        "total_modules": 3,
        "total_questions": 30,
        "total_answered": 15,
        "overall_progress": 50.0
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = request.user
        
        # 获取所有听力简答类型的模块
        modules = ExamModule.objects.filter(
            module_type='LISTENING_SA',
            is_activate=True
        ).prefetch_related('module_lsa__questions').order_by('display_order', 'id')
        
        modules_data = []
        total_questions = 0
        total_answered = 0
        
        # 检查用户是否已登录
        is_authenticated = user.is_authenticated
        
        for module in modules:
            # 获取该模块关联的所有对话
            dialogs = module.module_lsa.filter(is_active=True).order_by('display_order')
            
            # 统计该模块的所有问题
            module_question_count = 0
            module_answered_count = 0
            
            dialogs_data = []
            for dialog in dialogs:
                # 获取该对话的所有激活问题
                questions = dialog.questions.filter(is_active=True).order_by('display_order')
                question_count = questions.count()
                module_question_count += question_count
                
                # 序列化音频信息
                audio_info = None
                if dialog.audio_asset:
                    audio_info = {
                        'id': dialog.audio_asset.id,
                        'uri': dialog.audio_asset.uri,
                        'duration_ms': dialog.audio_asset.duration_ms
                    }
                
                # 序列化问题
                questions_data = []
                for question in questions:
                    # 如果用户登录，检查该题目是否已答
                    is_answered = False
                    if is_authenticated:
                        is_answered = LsaResponse.objects.filter(
                            user=user,
                            question=question
                        ).exists()
                        if is_answered:
                            module_answered_count += 1
                    
                    questions_data.append({
                        'id': question.id,
                        'question_type': question.question_type,
                        'question_text': question.question_text,
                        'option_a': question.option_a,
                        'option_b': question.option_b,
                        'option_c': question.option_c,
                        'option_d': question.option_d,
                        'display_order': question.display_order,
                        'is_answered': is_answered if is_authenticated else None
                    })
                
                dialogs_data.append({
                    'id': dialog.id,
                    'title': dialog.title,
                    'description': dialog.description,
                    'audio_asset': dialog.audio_asset_id if dialog.audio_asset else None,
                    'audio_info': audio_info,
                    'display_order': dialog.display_order,
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
                'dialog_count': len(dialogs_data),
                'question_count': module_question_count,
                'answered_count': module_answered_count,
                'progress': progress,
                'duration': module.duration,
                'score': module.score,
                'dialogs': dialogs_data,
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


class LsaSubmitAnswerView(APIView, ResponseMixin):
    """
    提交LSA听力简答答题
    
    POST /api/lsa/submit/
    
    请求体：
    {
        "question_id": 1,
        "answer_audio_id": 2,  // 可选
        "mode_type": "practice",  // practice 或 exam
        "is_timeout": false
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
        
        # 验证参数
        if not question_id:
            return self.error_response(message='缺少参数: question_id')
        
        try:
            question = LsaQuestion.objects.get(id=question_id)
        except LsaQuestion.DoesNotExist:
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
        response = LsaResponse.objects.create(
            user=user,
            question=question,
            answer_audio=answer_audio,
            mode_type=mode_type,
            is_timeout=is_timeout
        )
        
        return self.success_response(
            data={
                'response_id': response.id,
                'is_timeout': is_timeout
            },
            message='答题记录已保存'
        )


# ==================== LsaDialog 视图 ====================

class LsaDialogListView(APIView, ResponseMixin):
    """
    LSA对话列表视图（分页查询）
    
    GET /api/lsa/dialog/list/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        is_active = request.query_params.get('is_active')
        search = request.query_params.get('search')
        
        queryset = LsaDialog.objects.all()
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        queryset = queryset.order_by('display_order', '-created_at')
        
        paginator = LsaPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = LsaDialogSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = LsaDialogSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class LsaDialogDetailView(APIView, ResponseMixin):
    """
    LSA对话详情视图
    
    GET /api/lsa/dialog/detail/<id>/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            dialog = LsaDialog.objects.get(pk=pk)
            serializer = LsaDialogDetailSerializer(dialog)
            return self.success_response(data=serializer.data, message='查询成功')
        except LsaDialog.DoesNotExist:
            return self.not_found_response(message='对话不存在')


class LsaDialogQuestionsView(APIView, ResponseMixin):
    """
    获取对话的所有问题
    
    GET /api/lsa/dialog/<dialog_id>/questions/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, dialog_id):
        try:
            dialog = LsaDialog.objects.get(pk=dialog_id)
        except LsaDialog.DoesNotExist:
            return self.not_found_response(message='对话不存在')
        
        is_active_param = request.query_params.get('is_active', 'true')
        is_active = is_active_param.lower() == 'true'
        
        if is_active:
            questions = dialog.questions.filter(is_active=True).order_by('display_order')
        else:
            questions = dialog.questions.all().order_by('display_order')
        
        serializer = LsaQuestionSerializer(questions, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


# ==================== LsaQuestion 视图 ====================

class LsaQuestionListView(APIView, ResponseMixin):
    """
    LSA问题列表视图
    
    GET /api/lsa/question/list/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        is_active = request.query_params.get('is_active')
        dialog = request.query_params.get('dialog')
        question_type = request.query_params.get('question_type')
        
        queryset = LsaQuestion.objects.select_related('dialog').all()
        
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        if dialog:
            queryset = queryset.filter(dialog_id=dialog)
        
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        
        queryset = queryset.order_by('dialog', 'display_order')
        
        paginator = LsaPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = LsaQuestionSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = LsaQuestionSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class LsaQuestionDetailView(APIView, ResponseMixin):
    """
    LSA问题详情视图
    
    GET /api/lsa/question/detail/<id>/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            question = LsaQuestion.objects.get(pk=pk)
            serializer = LsaQuestionSerializer(question)
            return self.success_response(data=serializer.data, message='查询成功')
        except LsaQuestion.DoesNotExist:
            return self.not_found_response(message='问题不存在')


# ==================== LsaResponse 视图 ====================

class LsaResponseListView(APIView, ResponseMixin):
    """
    LSA回答列表视图
    
    GET /api/lsa/response/list/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.query_params.get('user')
        question = request.query_params.get('question')
        is_timeout = request.query_params.get('is_timeout')
        
        queryset = LsaResponse.objects.select_related('question', 'user').all()
        
        if user:
            queryset = queryset.filter(user_id=user)
        
        if question:
            queryset = queryset.filter(question_id=question)
        
        if is_timeout is not None:
            is_timeout_bool = is_timeout.lower() == 'true'
            queryset = queryset.filter(is_timeout=is_timeout_bool)
        
        queryset = queryset.order_by('-created_at')
        
        paginator = LsaPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = LsaResponseSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = LsaResponseSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')
