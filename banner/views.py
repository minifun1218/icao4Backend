"""
Banner 视图
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone

from common.response import ApiResponse
from common.mixins import ResponseMixin
from .models import Banner, BannerItem
from .serializers import (
    BannerSerializer,
    BannerDetailSerializer,
    BannerListSerializer,
    BannerItemSerializer
)


class BannerPagination(PageNumberPagination):
    """
    Banner分页类
    """
    page_size = 10  # 每页显示10条
    page_size_query_param = 'page_size'  # 允许客户端通过page_size参数自定义每页数量
    max_page_size = 100  # 最大每页100条
    page_query_param = 'page'  # 页码参数名


class BannerListView(APIView, ResponseMixin):
    """
    Banner列表视图（分页查询）
    
    GET /api/banner/list/
    Query参数:
        - page: 页码（默认1）
        - page_size: 每页数量（默认10，最大100）
        - is_active: 是否启用（可选，true/false）
        - status: 状态过滤（可选：ACTIVE/INACTIVE/SCHEDULED/EXPIRED）
        - search: 搜索关键词（搜索名称和描述）
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {
            "count": 总数,
            "next": 下一页URL,
            "previous": 上一页URL,
            "results": [Banner列表]
        }
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 获取查询参数
        is_active = request.query_params.get('is_active')
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search')
        
        # 基础查询集
        queryset = Banner.objects.all()
        
        # 过滤条件
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # 搜索
        if search:
            queryset = queryset.filter(
                name__icontains=search
            ) | queryset.filter(
                description__icontains=search
            )
        
        # 状态过滤（需要在Python层面处理，因为状态是动态计算的）
        if status_filter:
            filtered_ids = []
            for banner in queryset:
                if banner.get_current_status() == status_filter:
                    filtered_ids.append(banner.id)
            queryset = queryset.filter(id__in=filtered_ids)
        
        # 分页
        paginator = BannerPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = BannerListSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message='查询成功'
            )
        
        # 如果不分页
        serializer = BannerListSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


class BannerDetailView(APIView, ResponseMixin):
    """
    Banner详情视图（包含所有项目）
    
    GET /api/banner/detail/<id>/
    
    返回:
    {
        "code": 200,
        "message": "success",
        "data": {Banner详细信息，包含items列表}
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            banner = Banner.objects.get(pk=pk)
            serializer = BannerDetailSerializer(banner)
            return self.success_response(
                data=serializer.data,
                message='查询成功'
            )
        except Banner.DoesNotExist:
            return self.not_found_response(
                message='Banner不存在'
            )


class BannerActiveListView(APIView, ResponseMixin):
    """
    获取当前应该显示的Banner列表（前端展示用）
    
    GET /api/banner/active/
    Query参数:
        - page: 页码（可选）
        - page_size: 每页数量（可选）
    
    返回所有启用且在显示时间范围内的Banner
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 获取所有启用的Banner
        queryset = Banner.objects.filter(is_active=True)
        
        # 过滤出应该显示的Banner
        now = timezone.now()
        active_banners = []
        
        for banner in queryset:
            # 检查时间范围
            if banner.start_time and now < banner.start_time:
                continue
            if banner.end_time and now > banner.end_time:
                continue
            active_banners.append(banner)
        
        # 转换为queryset
        active_ids = [b.id for b in active_banners]
        queryset = Banner.objects.filter(id__in=active_ids)
        
        # 分页（可选）
        if request.query_params.get('page'):
            paginator = BannerPagination()
            page = paginator.paginate_queryset(queryset, request)
            if page is not None:
                serializer = BannerDetailSerializer(page, many=True)
                result = paginator.get_paginated_response(serializer.data)
                return self.success_response(
                    data=result.data,
                    message='查询成功'
                )
        
        # 不分页，返回所有
        serializer = BannerDetailSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


class BannerItemListView(APIView, ResponseMixin):
    """
    获取指定Banner的所有项目
    
    GET /api/banner/<banner_id>/items/
    Query参数:
        - is_enabled: 是否只显示启用的项目（可选，默认true）
    
    返回指定Banner的所有项目列表
    """
    permission_classes = [AllowAny]
    
    def get(self, request, banner_id):
        try:
            banner = Banner.objects.get(pk=banner_id)
        except Banner.DoesNotExist:
            return self.not_found_response(
                message='Banner不存在'
            )
        
        # 获取is_enabled参数
        is_enabled_param = request.query_params.get('is_enabled', 'true')
        is_enabled = is_enabled_param.lower() == 'true'
        
        # 查询项目
        if is_enabled:
            items = banner.banneritem_set.filter(is_enabled=True)
        else:
            items = banner.banneritem_set.all()
        
        # 序列化
        serializer = BannerItemSerializer(items, many=True)
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )


class BannerSearchView(APIView, ResponseMixin):
    """
    Banner搜索视图
    
    GET /api/banner/search/
    Query参数:
        - q: 搜索关键词（必需）
        - page: 页码（可选）
        - page_size: 每页数量（可选）
    
    在Banner的名称和描述中搜索
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return self.bad_request_response(
                message='搜索关键词不能为空'
            )
        
        # 搜索
        queryset = Banner.objects.filter(
            name__icontains=query
        ) | Banner.objects.filter(
            description__icontains=query
        )
        
        # 去重
        queryset = queryset.distinct()
        
        # 分页
        paginator = BannerPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = BannerListSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message=f'搜索到 {queryset.count()} 条结果'
            )
        
        # 不分页
        serializer = BannerListSerializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message=f'搜索到 {queryset.count()} 条结果'
        )


class BannerItemAllListView(APIView, ResponseMixin):
    """
    所有BannerItem列表视图（分页查询）
    
    GET /api/banner/items/list/
    Query参数:
        - page: 页码（默认1）
        - page_size: 每页数量（默认10，最大100）
        - is_enabled: 是否启用（可选，true/false）
        - banner: Banner ID过滤（可选）
        - search: 搜索关键词（搜索标题和描述）
    
    返回所有BannerItem列表
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 获取查询参数
        is_enabled = request.query_params.get('is_enabled')
        banner_id = request.query_params.get('banner')
        search = request.query_params.get('search')
        
        # 基础查询集，预加载关联的banner
        queryset = BannerItem.objects.select_related('banner').all()
        
        # 过滤条件
        if is_enabled is not None:
            is_enabled_bool = is_enabled.lower() == 'true'
            queryset = queryset.filter(is_enabled=is_enabled_bool)
        
        if banner_id:
            queryset = queryset.filter(banner_id=banner_id)
        
        # 搜索
        if search:
            queryset = queryset.filter(
                title__icontains=search
            ) | queryset.filter(
                description__icontains=search
            )
        
        # 分页
        paginator = BannerPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = BannerItemSerializer(page, many=True, context={'request': request})
            result = paginator.get_paginated_response(serializer.data)
            return self.success_response(
                data=result.data,
                message='查询成功'
            )
        
        # 如果不分页
        serializer = BannerItemSerializer(queryset, many=True, context={'request': request})
        return self.success_response(
            data=serializer.data,
            message='查询成功'
        )