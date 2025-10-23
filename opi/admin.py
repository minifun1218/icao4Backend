"""
OPI (口语面试) Admin 配置
"""
from django.contrib import admin
from .models import OpiTopic, OpiQuestion, OpiResponse


class OpiQuestionInline(admin.TabularInline):
    """
    OPI问题内联编辑
    """
    model = OpiQuestion
    extra = 1
    fields = ['QOrder', 'prompt_audio']
    ordering = ['QOrder']


@admin.register(OpiTopic)
class OpiTopicAdmin(admin.ModelAdmin):
    """
    OPI话题后台管理
    """
    list_display = [
        'id',
        'title',
        'order',
        'question_count',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['title', 'description']
    ordering = ['order', '-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'order')
        }),
        ('关联模块', {
            'fields': ('exam_module',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    filter_horizontal = ['exam_module']
    
    inlines = [OpiQuestionInline]
    
    def question_count(self, obj):
        """显示问题数量"""
        return obj.questions.count()
    question_count.short_description = '问题数量'


@admin.register(OpiQuestion)
class OpiQuestionAdmin(admin.ModelAdmin):
    """
    OPI问题后台管理
    """
    list_display = [
        'id',
        'topic',
        'QOrder',
        'prompt_audio',
        'response_count',
        'created_at'
    ]
    list_filter = ['topic', 'created_at']
    search_fields = ['topic__title']
    ordering = ['topic', 'QOrder']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('topic', 'QOrder')
        }),
        ('音频资源', {
            'fields': ('prompt_audio',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def response_count(self, obj):
        """显示回答数量"""
        return obj.responses.count()
    response_count.short_description = '回答数量'


@admin.register(OpiResponse)
class OpiResponseAdmin(admin.ModelAdmin):
    """
    OPI回答后台管理
    """
    list_display = [
        'id',
        'question',
        'user',
        'score',
        'is_timeout',
        'answered_at',
        'created_at'
    ]
    list_filter = ['is_timeout', 'answered_at', 'created_at']
    search_fields = ['user__username', 'question__topic__title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('question', 'user')
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
