"""
Banner Admin 配置
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Banner, BannerItem


class BannerItemInline(admin.TabularInline):
    """
    Banner项目内联编辑
    """
    model = BannerItem
    extra = 1
    fields = ['title', 'image', 'link_url', 'sort_weight', 'is_enabled']
    readonly_fields = ['image']


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """
    Banner后台管理
    """
    list_display = [
        'id',
        'name',
        'sort_order',
        'is_active',
        'start_time',
        'end_time',
        'get_current_status',
        'get_item_count',
        'created_at'
    ]
    list_filter = ['is_active', 'created_at', 'start_time', 'end_time']
    search_fields = ['name', 'description']
    ordering = ['-sort_order', '-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'sort_order')
        }),
        ('显示设置', {
            'fields': ('is_active', 'start_time', 'end_time')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [BannerItemInline]
    
    def get_current_status(self, obj):
        """显示当前状态"""
        return obj.get_current_status()
    get_current_status.short_description = '当前状态'
    
    def get_item_count(self, obj):
        """显示项目数量"""
        return obj.get_item_count()
    get_item_count.short_description = '项目数量'


@admin.register(BannerItem)
class BannerItemAdmin(admin.ModelAdmin):
    """
    BannerItem后台管理
    """
    list_display = [
        'id',
        'title',
        'banner',
        'image_thumbnail',
        'sort_weight',
        'is_enabled',
        'created_at'
    ]
    list_filter = ['is_enabled', 'banner', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-sort_weight', '-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('banner', 'title', 'description')
        }),
        ('图片和链接', {
            'fields': ('image', 'image_preview', 'link_url')
        }),
        ('显示设置', {
            'fields': ('sort_weight', 'is_enabled')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    def image_thumbnail(self, obj):
        """列表页显示缩略图"""
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return '-'
    image_thumbnail.short_description = '图片预览'
    
    def image_preview(self, obj):
        """详情页显示大图预览"""
        if obj.image:
            return format_html('<img src="{}" width="300" style="max-width: 100%;" />', obj.image.url)
        return '-'
    image_preview.short_description = '图片预览'
