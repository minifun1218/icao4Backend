"""
Story (故事复述) Admin 配置
"""
from django.contrib import admin
from .models import RetellItem, RetellResponse


@admin.register(RetellItem)
class RetellItemAdmin(admin.ModelAdmin):
    """
    复述题目后台管理
    """
    list_display = [
        'id',
        'title',
        'audio_asset',
        'response_count',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title',)
        }),
        ('音频资源', {
            'fields': ('audio_asset',)
        }),
        ('关联模块', {
            'fields': ('exam_modules',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    filter_horizontal = ['exam_modules']
    
    def response_count(self, obj):
        """显示回答数量"""
        return obj.responses.count()
    response_count.short_description = '回答数量'


@admin.register(RetellResponse)
class RetellResponseAdmin(admin.ModelAdmin):
    """
    复述回答后台管理
    """
    list_display = [
        'id',
        'retell_item',
        'user',
        'score',
        'is_timeout',
        'answered_at',
        'created_at'
    ]
    list_filter = ['is_timeout', 'answered_at', 'created_at']
    search_fields = ['user__username', 'retell_item__title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('retell_item', 'user')
        }),
        ('回答信息', {
            'fields': ('answer_audio', 'score', 'is_timeout', 'answered_at')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'answered_at']
