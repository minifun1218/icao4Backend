"""
Term (航空术语) Admin 配置
"""
from django.contrib import admin
from .models import AvTermsTopic, AvTerm


@admin.register(AvTermsTopic)
class AvTermsTopicAdmin(admin.ModelAdmin):
    """
    航空术语主题后台管理
    """
    list_display = [
        'id',
        'code',
        'name_zh',
        'name_en',
        'display_order',
        'term_count',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['code', 'name_zh', 'name_en', 'description']
    ordering = ['display_order', 'id']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name_zh', 'name_en')
        }),
        ('详细信息', {
            'fields': ('description', 'display_order')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def term_count(self, obj):
        """显示术语数量"""
        return obj.terms.count()
    term_count.short_description = '术语数量'


@admin.register(AvTerm)
class AvTermAdmin(admin.ModelAdmin):
    """
    航空术语后台管理
    """
    list_display = [
        'id',
        'headword',
        'ipa',
        'cefr_level',
        'topic',
        'audio_asset',
        'created_at'
    ]
    list_filter = ['cefr_level', 'topic', 'created_at']
    search_fields = ['headword', 'definition_zh', 'definition_en']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('headword', 'ipa', 'cefr_level')
        }),
        ('释义信息', {
            'fields': ('definition_zh', 'definition_en')
        }),
        ('例句信息', {
            'fields': ('example_en', 'example_zh')
        }),
        ('关联信息', {
            'fields': ('topic', 'audio_asset')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
