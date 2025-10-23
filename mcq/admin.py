"""
MCQ (听力选择题) Admin 配置
"""
from django.contrib import admin
from .models import McqQuestion, McqChoice, McqResponse


class McqChoiceInline(admin.TabularInline):
    """
    选择题选项内联编辑
    """
    model = McqChoice
    extra = 4
    max_num = 4
    fields = ['label', 'content', 'is_correct']
    ordering = ['label']


@admin.register(McqQuestion)
class McqQuestionAdmin(admin.ModelAdmin):
    """
    听力选择题后台管理
    """
    list_display = [
        'id',
        'text_stem_short',
        'audio_asset',
        'choice_count',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['text_stem']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('text_stem',)
        }),
        ('音频资源', {
            'fields': ('audio_asset',)
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
    
    inlines = [McqChoiceInline]
    
    def text_stem_short(self, obj):
        """显示题干缩略"""
        if obj.text_stem:
            return obj.text_stem[:50] + '...' if len(obj.text_stem) > 50 else obj.text_stem
        return '-'
    text_stem_short.short_description = '题干'
    
    def choice_count(self, obj):
        """显示选项数量"""
        return obj.choices.count()
    choice_count.short_description = '选项数量'


@admin.register(McqChoice)
class McqChoiceAdmin(admin.ModelAdmin):
    """
    选择题选项后台管理
    """
    list_display = [
        'id',
        'question',
        'label',
        'content_short',
        'is_correct'
    ]
    list_filter = ['is_correct', 'label']
    search_fields = ['content', 'question__text_stem']
    ordering = ['question', 'label']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('question', 'label', 'content')
        }),
        ('答案信息', {
            'fields': ('is_correct',)
        }),
    )
    
    def content_short(self, obj):
        """显示内容缩略"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = '选项内容'


@admin.register(McqResponse)
class McqResponseAdmin(admin.ModelAdmin):
    """
    选择题作答记录后台管理
    """
    list_display = [
        'id',
        'question',
        'user',
        'selected_choice',
        'is_correct',
        'is_timeout',
        'answered_at',
        'created_at'
    ]
    list_filter = ['is_correct', 'is_timeout', 'answered_at', 'created_at']
    search_fields = ['user__username', 'question__text_stem']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('question', 'user')
        }),
        ('回答信息', {
            'fields': ('selected_choice', 'is_correct', 'is_timeout', 'answered_at')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'answered_at']
