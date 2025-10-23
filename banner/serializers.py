"""
Banner 序列化器
"""
from rest_framework import serializers
from .models import Banner, BannerItem


class BannerItemSerializer(serializers.ModelSerializer):
    """
    Banner项目序列化器（带Banner信息）
    """
    image_url = serializers.SerializerMethodField()
    banner_info = serializers.SerializerMethodField()
    
    class Meta:
        model = BannerItem
        fields = [
            'id',
            'banner',
            'banner_info',
            'title',
            'description',
            'image',
            'image_url',
            'link_url',
            'sort_weight',
            'is_enabled',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'image_url', 'banner_info']
    
    def get_image_url(self, obj):
        """获取图片完整URL"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_banner_info(self, obj):
        """获取所属Banner信息"""
        if obj.banner:
            return {
                'id': obj.banner.id,
                'name': obj.banner.name,
                'is_active': obj.banner.is_active
            }
        return None


class BannerSerializer(serializers.ModelSerializer):
    """
    Banner序列化器
    """
    # 当前状态（通过方法字段动态获取）
    current_status = serializers.SerializerMethodField()
    # 剩余显示时间（分钟）
    remaining_minutes = serializers.SerializerMethodField()
    # Banner项目数量
    item_count = serializers.SerializerMethodField()
    # 是否应该显示
    should_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Banner
        fields = [
            'id',
            'name',
            'description',
            'sort_order',
            'is_active',
            'start_time',
            'end_time',
            'created_at',
            'updated_at',
            'current_status',
            'remaining_minutes',
            'item_count',
            'should_display'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_current_status(self, obj):
        """获取当前状态"""
        return obj.get_current_status()
    
    def get_remaining_minutes(self, obj):
        """获取剩余显示时间（分钟）"""
        return obj.get_remaining_display_minutes()
    
    def get_item_count(self, obj):
        """获取项目数量"""
        return obj.get_item_count()
    
    def get_should_display(self, obj):
        """是否应该显示"""
        return obj.should_display()


class BannerDetailSerializer(BannerSerializer):
    """
    Banner详情序列化器（包含所有项目）
    """
    # 嵌套Banner项目列表
    items = serializers.SerializerMethodField()
    
    class Meta(BannerSerializer.Meta):
        fields = BannerSerializer.Meta.fields + ['items']
    
    def get_items(self, obj):
        """获取启用的Banner项目列表"""
        # 获取所有启用的项目，按sort_weight降序排列
        items = obj.banneritem_set.filter(is_enabled=True).order_by('-sort_weight')
        return BannerItemSerializer(items, many=True).data


class BannerListSerializer(serializers.ModelSerializer):
    """
    Banner列表序列化器（简化版，用于列表页）
    """
    current_status = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Banner
        fields = [
            'id',
            'name',
            'description',
            'sort_order',
            'is_active',
            'start_time',
            'end_time',
            'current_status',
            'item_count',
            'created_at'
        ]
    
    def get_current_status(self, obj):
        """获取当前状态"""
        return obj.get_current_status()
    
    def get_item_count(self, obj):
        """获取项目数量"""
        return obj.get_item_count()

