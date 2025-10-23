"""
Story (故事复述) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from common.response import ApiResponse
from common.mixins import ResponseMixin
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
