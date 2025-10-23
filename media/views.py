"""
Media (媒体资源) 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from common.response import ApiResponse
from common.mixins import ResponseMixin
from .models import MediaAsset
from .serializers import MediaAssetSerializer


class MediaPagination(PageNumberPagination):
    """Media分页类"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class MediaAssetListView(APIView, ResponseMixin):
    """
    媒体资源列表视图（分页查询）
    
    GET /api/media/asset/list/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        media_type = request.query_params.get('media_type')
        search = request.query_params.get('search')
        
        queryset = MediaAsset.objects.all()
        
        if media_type:
            queryset = queryset.filter(media_type=media_type)
        
        if search:
            queryset = queryset.filter(uri__icontains=search)
        
        queryset = queryset.order_by('-created_at')
        
        paginator = MediaPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = MediaAssetSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = MediaAssetSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')


class MediaAssetDetailView(APIView, ResponseMixin):
    """
    媒体资源详情视图
    
    GET /api/media/asset/detail/<id>/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            asset = MediaAsset.objects.get(pk=pk)
            serializer = MediaAssetSerializer(asset)
            return self.success_response(data=serializer.data, message='查询成功')
        except MediaAsset.DoesNotExist:
            return self.not_found_response(message='媒体资源不存在')


class MediaTypeListView(APIView, ResponseMixin):
    """
    获取所有媒体类型
    
    GET /api/media/types/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        types = [
            {
                'value': code,
                'label': label
            }
            for code, label in MediaAsset.MEDIA_TYPE
        ]
        
        return self.success_response(data=types, message='查询成功')


class MediaAssetsByTypeView(APIView, ResponseMixin):
    """
    按类型获取媒体资源
    
    GET /api/media/asset/type/<media_type>/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, media_type):
        queryset = MediaAsset.objects.filter(media_type=media_type).order_by('-created_at')
        
        paginator = MediaPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = MediaAssetSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(data=result.data, message='查询成功')
        
        serializer = MediaAssetSerializer(queryset, many=True)
        return self.success_response(data=serializer.data, message='查询成功')
