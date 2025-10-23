"""
MCQ (听力选择题) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from common.response import ApiResponse
from common.mixins import ResponseMixin
from .models import McqQuestion, McqChoice, McqResponse
from .serializers import (
    McqQuestionSerializer,
    McqQuestionDetailSerializer,
    McqChoiceSerializer,
    McqResponseSerializer
)


class McqPagination(PageNumberPagination):
    """MCQ分页类"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# ==================== McqQuestion 视图 ====================

class McqQuestionListView(APIView, ResponseMixin):
    """
    听力选择题列表视图（分页查询）
    
    GET /api/mcq/question/list/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        search = request.query_params.get('search')
        
        queryset = McqQuestion.objects.all()
        
        if search:
            queryset = queryset.filter(text_stem__icontains=search)
        
        queryset = queryset.order_by('-created_at')
        
        paginator = McqPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = McqQuestionSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = McqQuestionSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class McqQuestionDetailView(APIView, ResponseMixin):
    """
    听力选择题详情视图（包含所有选项）
    
    GET /api/mcq/question/detail/<id>/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            question = McqQuestion.objects.prefetch_related('choices').get(pk=pk)
            serializer = McqQuestionDetailSerializer(question)
            return self.success_response(data=serializer.data, message='查询成功')
        except McqQuestion.DoesNotExist:
            return self.not_found_response(message='题目不存在')


class McqQuestionChoicesView(APIView, ResponseMixin):
    """
    获取题目的所有选项
    
    GET /api/mcq/question/<question_id>/choices/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, question_id):
        try:
            question = McqQuestion.objects.get(pk=question_id)
        except McqQuestion.DoesNotExist:
            return self.not_found_response(message='题目不存在')
        
        choices = question.choices.all().order_by('label')
        serializer = McqChoiceSerializer(choices, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


# ==================== McqChoice 视图 ====================

class McqChoiceListView(APIView, ResponseMixin):
    """
    选择题选项列表视图
    
    GET /api/mcq/choice/list/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        question = request.query_params.get('question')
        
        queryset = McqChoice.objects.select_related('question').all()
        
        if question:
            queryset = queryset.filter(question_id=question)
        
        queryset = queryset.order_by('question', 'label')
        
        paginator = McqPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = McqChoiceSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = McqChoiceSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


# ==================== McqResponse 视图 ====================

class McqResponseListView(APIView, ResponseMixin):
    """
    选择题作答记录列表视图
    
    GET /api/mcq/response/list/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.query_params.get('user')
        question = request.query_params.get('question')
        is_correct = request.query_params.get('is_correct')
        is_timeout = request.query_params.get('is_timeout')
        
        queryset = McqResponse.objects.select_related('question', 'user', 'selected_choice').all()
        
        if user:
            queryset = queryset.filter(user_id=user)
        
        if question:
            queryset = queryset.filter(question_id=question)
        
        if is_correct is not None:
            is_correct_bool = is_correct.lower() == 'true'
            queryset = queryset.filter(is_correct=is_correct_bool)
        
        if is_timeout is not None:
            is_timeout_bool = is_timeout.lower() == 'true'
            queryset = queryset.filter(is_timeout=is_timeout_bool)
        
        queryset = queryset.order_by('-created_at')
        
        paginator = McqPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = McqResponseSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = McqResponseSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class McqResponseDetailView(APIView, ResponseMixin):
    """
    作答记录详情视图
    
    GET /api/mcq/response/detail/<id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            response = McqResponse.objects.select_related('question', 'user', 'selected_choice').get(pk=pk)
            serializer = McqResponseSerializer(response)
            return self.success_response(data=serializer.data, message='查询成功')
        except McqResponse.DoesNotExist:
            return self.not_found_response(message='作答记录不存在')
