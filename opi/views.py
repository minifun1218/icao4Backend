"""
OPI (口语面试) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from common.response import ApiResponse
from common.mixins import ResponseMixin
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
