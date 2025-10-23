"""
Account Admin 配置
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Role, WxUser, UserLearningProgress


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    角色后台管理
    """
    list_display = [
        'id',
        'name',
        'code',
        'status_display',
        'created_at',
        'updated_at'
    ]
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'code', 'description')
        }),
        ('状态信息', {
            'fields': ('status',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def status_display(self, obj):
        """显示状态"""
        return '激活' if obj.status == 1 else '禁用'
    status_display.short_description = '状态'
    status_display.admin_order_field = 'status'


@admin.register(WxUser)
class WxUserAdmin(admin.ModelAdmin):
    """
    微信用户后台管理
    """
    list_display = [
        'id',
        'username',
        'avatar_thumbnail',
        'openid_short',
        'phone',
        'gender_display',
        'level',
        'status_display',
        'join_date',
        'last_login',
        'created_at'
    ]
    list_filter = ['status', 'gender', 'level', 'join_date', 'created_at']
    search_fields = ['username', 'openid', 'phone', 'location']
    ordering = ['-created_at']
    
    readonly_fields = ['openid', 'created_at', 'updated_at', 'last_login', 'avatar_preview']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('openid', 'username', 'phone', 'avatar', 'avatar_preview')
        }),
        ('个人信息', {
            'fields': ('gender', 'birthday', 'location', 'level')
        }),
        ('状态信息', {
            'fields': ('status', 'join_date', 'last_login')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def openid_short(self, obj):
        """显示openid缩略"""
        return obj.openid[:20] + '...' if len(obj.openid) > 20 else obj.openid
    openid_short.short_description = 'OpenID'
    
    def gender_display(self, obj):
        """显示性别"""
        gender_map = {1: '男', 2: '女', 0: '未知'}
        return gender_map.get(obj.gender, '-')
    gender_display.short_description = '性别'
    gender_display.admin_order_field = 'gender'
    
    def status_display(self, obj):
        """显示状态"""
        return '正常' if obj.status == 1 else '禁用'
    status_display.short_description = '状态'
    status_display.admin_order_field = 'status'
    
    def avatar_thumbnail(self, obj):
        """列表页显示头像缩略图"""
        if obj.avatar:
            return format_html('<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />', obj.avatar.url)
        return '-'
    avatar_thumbnail.short_description = '头像'
    
    def avatar_preview(self, obj):
        """详情页显示头像大图"""
        if obj.avatar:
            return format_html('<img src="{}" width="150" style="border-radius: 10px; max-width: 100%;" />', obj.avatar.url)
        return '-'
    avatar_preview.short_description = '头像预览'


@admin.register(UserLearningProgress)
class UserLearningProgressAdmin(admin.ModelAdmin):
    """
    用户学习进度后台管理
    """
    list_display = [
        'id',
        'user',
        'get_overall_progress_display',
        'continuous_days',
        'total_study_time',
        'total_practice_count',
        'total_exam_count',
        'last_study_date',
        'updated_at'
    ]
    list_filter = ['last_study_date', 'updated_at']
    search_fields = ['user__username', 'user__openid']
    ordering = ['-updated_at']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('用户信息', {
            'fields': ('user',)
        }),
        ('MCQ进度', {
            'fields': ('mcq_total', 'mcq_completed', 'mcq_correct', 'mcq_practice_count', 'mcq_exam_count')
        }),
        ('LSA进度', {
            'fields': ('lsa_total', 'lsa_completed', 'lsa_practice_count', 'lsa_exam_count')
        }),
        ('Story进度', {
            'fields': ('story_total', 'story_completed', 'story_avg_score', 'story_practice_count', 'story_exam_count')
        }),
        ('OPI进度', {
            'fields': ('opi_total', 'opi_completed', 'opi_avg_score', 'opi_practice_count', 'opi_exam_count')
        }),
        ('ATC进度', {
            'fields': ('atc_total', 'atc_completed', 'atc_avg_score', 'atc_practice_count', 'atc_exam_count')
        }),
        ('总体统计', {
            'fields': ('total_study_time', 'total_practice_count', 'total_exam_count', 'continuous_days', 'last_study_date')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_overall_progress_display(self, obj):
        """显示总体进度"""
        progress = obj.get_overall_progress()
        return f'{progress}%'
    get_overall_progress_display.short_description = '总体进度'
    get_overall_progress_display.admin_order_field = 'mcq_completed'
