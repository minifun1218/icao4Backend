"""
Exam Admin 配置
"""
from django.contrib import admin
from .models import ExamPaper, ExamModule


class ExamModuleInline(admin.TabularInline):
    """
    考试模块内联编辑
    """
    model = ExamModule.exam_paper.through
    extra = 1
    verbose_name = '考试模块'
    verbose_name_plural = '考试模块'


@admin.register(ExamPaper)
class ExamPaperAdmin(admin.ModelAdmin):
    """
    考试试卷后台管理
    """
    list_display = [
        'id',
        'code',
        'name',
        'total_duration_min',
        'module_count',
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['code', 'name', 'description']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'description')
        }),
        ('考试时长', {
            'fields': ('total_duration_min',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    inlines = [ExamModuleInline]
    
    def module_count(self, obj):
        """显示模块数量"""
        return obj.exammodule_set.filter(is_activate=True).count()
    module_count.short_description = '模块数量'


@admin.register(ExamModule)
class ExamModuleAdmin(admin.ModelAdmin):
    """
    考试模块后台管理
    """
    list_display = [
        'id',
        'get_module_type_display',
        'display_order',
        'score',
        'duration',
        'is_activate',
        'created_at'
    ]
    list_filter = ['is_activate', 'module_type', 'created_at']
    search_fields = ['module_type']
    ordering = ['display_order', '-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('module_type', 'display_order')
        }),
        ('评分和时长', {
            'fields': ('score', 'duration')
        }),
        ('关联试卷', {
            'fields': ('exam_paper',)
        }),
        ('配置信息', {
            'fields': ('is_activate',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    filter_horizontal = ['exam_paper']  # 多对多字段使用水平过滤器
    
    def get_module_type_display(self, obj):
        """显示模块类型"""
        return obj.get_module_type_display()
    get_module_type_display.short_description = '模块类型'
