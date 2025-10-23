"""
LSA (听力简答) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from common.response import ApiResponse
from common.mixins import ResponseMixin
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
