"""
ATC Admin 配置
"""
from django.contrib import admin
from .models import Airport, AtcScenario, AtcTurn, AtcTurnResponse


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    """
    机场后台管理
    """
    list_display = [
        'id',
        'icao',
        'name',
        'city',
        'country',
        'timezone',
        'is_active',
        'scenario_count',
        'created_at'
    ]
    list_filter = ['is_active', 'country', 'created_at']
    search_fields = ['icao', 'name', 'city', 'country']
    ordering = ['icao']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('icao', 'name', 'city', 'country')
        }),
        ('配置信息', {
            'fields': ('timezone', 'is_active')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def scenario_count(self, obj):
        """显示场景数量"""
        return obj.scenarios.filter(is_active=True).count()
    scenario_count.short_description = '场景数量'


class AtcTurnInline(admin.TabularInline):
    """
    ATC轮次内联编辑
    """
    model = AtcTurn
    extra = 1
    fields = ['turn_number', 'speaker_type', 'audio', 'is_active']
    ordering = ['turn_number']


@admin.register(AtcScenario)
class AtcScenarioAdmin(admin.ModelAdmin):
    """
    ATC场景后台管理
    """
    list_display = [
        'id',
        'title',
        'airport',
        'module',
        'is_active',
        'turn_count',
        'created_at'
    ]
    list_filter = ['is_active', 'airport', 'module', 'created_at']
    search_fields = ['title', 'description', 'airport__name', 'airport__icao']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description')
        }),
        ('关联信息', {
            'fields': ('airport', 'module')
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
    
    inlines = [AtcTurnInline]
    
    def turn_count(self, obj):
        """显示轮次数量"""
        return obj.turns.filter(is_active=True).count()
    turn_count.short_description = '轮次数量'


@admin.register(AtcTurn)
class AtcTurnAdmin(admin.ModelAdmin):
    """
    ATC轮次后台管理
    """
    list_display = [
        'id',
        'scenario',
        'turn_number',
        'speaker_type',
        'audio',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'speaker_type', 'scenario', 'created_at']
    search_fields = ['scenario__title', 'turn_number']
    ordering = ['scenario', 'turn_number']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('scenario', 'turn_number', 'speaker_type')
        }),
        ('音频信息', {
            'fields': ('audio',)
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


@admin.register(AtcTurnResponse)
class AtcTurnResponseAdmin(admin.ModelAdmin):
    """
    ATC轮次回答后台管理
    """
    list_display = [
        'id',
        'atc_turn',
        'user',
        'score',
        'is_timeout',
        'created_at'
    ]
    list_filter = ['is_timeout', 'created_at']
    search_fields = ['user__username', 'atc_turn__scenario__title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('atc_turn', 'user')
        }),
        ('回答信息', {
            'fields': ('audio_file_path', 'is_timeout', 'score')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
