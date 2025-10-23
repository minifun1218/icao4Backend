"""
LSA (听力简答) Admin 配置
"""
from django.contrib import admin
from .models import LsaDialog, LsaQuestion, LsaResponse


class LsaQuestionInline(admin.TabularInline):
    """
    LSA问题内联编辑
    """
    model = LsaQuestion
    extra = 1
    fields = ['question_text', 'question_type', 'display_order', 'correct_answer', 'is_active']
    ordering = ['display_order']


@admin.register(LsaDialog)
class LsaDialogAdmin(admin.ModelAdmin):
    """
    听力简答对话后台管理
    """
    list_display = [
        'id',
        'title',
        'display_order',
        'audio_asset',
        'is_active',
        'question_count',
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['display_order', '-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'display_order')
        }),
        ('音频资源', {
            'fields': ('audio_asset',)
        }),
        ('关联模块', {
            'fields': ('exam_module',)
        }),
        ('配置信息', {
            'fields': ('is_active',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    filter_horizontal = ['exam_module']
    
    inlines = [LsaQuestionInline]
    
    def question_count(self, obj):
        """显示问题数量"""
        return obj.questions.filter(is_active=True).count()
    question_count.short_description = '问题数量'


@admin.register(LsaQuestion)
class LsaQuestionAdmin(admin.ModelAdmin):
    """
    听力简答问题后台管理
    """
    list_display = [
        'id',
        'dialog',
        'question_type',
        'display_order',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'question_type', 'dialog', 'created_at']
    search_fields = ['question_text', 'correct_answer']
    ordering = ['dialog', 'display_order']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('dialog', 'question_type', 'question_text')
        }),
        ('选项设置', {
            'fields': ('option_a', 'option_b', 'option_c', 'option_d')
        }),
        ('答案信息', {
            'fields': ('correct_answer', 'answer_explanation')
        }),
        ('配置信息', {
            'fields': ('display_order', 'is_active')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LsaResponse)
class LsaResponseAdmin(admin.ModelAdmin):
    """
    听力简答回答后台管理
    """
    list_display = [
        'id',
        'question',
        'user',
        'is_timeout',
        'answered_at',
        'created_at'
    ]
    list_filter = ['is_timeout', 'answered_at', 'created_at']
    search_fields = ['user__username', 'question__question_text']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('question', 'user')
        }),
        ('回答信息', {
            'fields': ('answer_audio', 'is_timeout', 'answered_at')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'answered_at']
