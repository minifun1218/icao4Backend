"""
ATC Admin 配置
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
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
            'fields': ('icao', 'name', 'city', 'country'),
            'description': '💡 提示：ICAO代码为国际民航组织四字代码'
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
        count = obj.scenarios.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<a href="/admin/atc/atcscenario/?airport__id__exact={}" style="color: #17a2b8;">{} 个场景</a>',
                obj.id, count
            )
        return '0 个场景'
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
            'fields': ('title', 'description'),
            'description': '💡 提示：场景的基本信息'
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
        count = obj.turns.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<a href="/admin/atc/atcturn/?scenario__id__exact={}" style="color: #17a2b8;">{} 个轮次</a>',
                obj.id, count
            )
        return '0 个轮次'
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
        'speaker_type_display',
        'audio_preview',
        'is_active',
        'response_count',
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
            'fields': ('audio', 'audio_player_display')
        }),
        ('配置信息', {
            'fields': ('is_active',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'audio_player_display']
    
    def speaker_type_display(self, obj):
        """显示说话者类型（带图标）"""
        if obj.speaker_type == 'pilot':
            return format_html(
                '<span style="color: #007bff;"><i class="fas fa-plane"></i> 飞行员</span>'
            )
        else:
            return format_html(
                '<span style="color: #28a745;"><i class="fas fa-tower-broadcast"></i> 管制员</span>'
            )
    speaker_type_display.short_description = '说话者'
    
    def audio_preview(self, obj):
        """列表页音频预览（可播放）"""
        if obj.audio:
            audio_url = obj.audio.get_file_url()
            return mark_safe(f'''
                <div style="display: flex; align-items: center; gap: 5px;">
                    <i class="fas fa-file-audio" style="font-size: 20px; color: #17a2b8;"></i>
                    <audio controls style="height: 30px; width: 180px;" preload="none">
                        <source src="{audio_url}" type="audio/mpeg">
                    </audio>
                </div>
            ''')
        return '-'
    audio_preview.short_description = '通讯音频'
    
    def audio_player_display(self, obj):
        """详情页音频播放器"""
        if obj.audio:
            audio_url = obj.audio.get_file_url()
            duration_display = ''
            if obj.audio.duration_ms:
                seconds = obj.audio.duration_ms / 1000
                if seconds < 60:
                    duration_display = f'{seconds:.1f}秒'
                else:
                    minutes = seconds / 60
                    duration_display = f'{minutes:.1f}分钟'
            
            speaker_color = '#007bff' if obj.speaker_type == 'pilot' else '#28a745'
            speaker_name = '飞行员' if obj.speaker_type == 'pilot' else '管制员'
            
            return mark_safe(f'''
                <div style="padding: 15px; background: #f0f8ff; border-left: 4px solid {speaker_color}; border-radius: 4px;">
                    <div style="margin-bottom: 10px;">
                        <i class="fas fa-volume-up" style="color: {speaker_color}; font-size: 24px;"></i>
                        <strong style="margin-left: 10px; font-size: 16px;">通讯音频 - {speaker_name}</strong>
                    </div>
                    <audio controls style="width: 100%; margin: 10px 0;">
                        <source src="{audio_url}" type="audio/mpeg">
                        您的浏览器不支持音频播放。
                    </audio>
                    <div style="color: #666; font-size: 12px; margin-top: 5px;">
                        {f'<i class="fas fa-clock"></i> 时长: {duration_display}' if duration_display else ''}
                        <br>
                        <a href="{audio_url}" target="_blank" download style="color: {speaker_color};">
                            <i class="fas fa-download"></i> 下载音频
                        </a>
                    </div>
                </div>
            ''')
        return mark_safe('<p style="color: #999;">未上传音频</p>')
    audio_player_display.short_description = '音频播放器'
    
    def response_count(self, obj):
        """显示回答数量"""
        count = obj.responses.count()
        if count > 0:
            return format_html(
                '<a href="/admin/atc/atcturnresponse/?atc_turn__id__exact={}" style="color: #17a2b8;">{} 个回答</a>',
                obj.id, count
            )
        return '0 个回答'
    response_count.short_description = '回答数量'


@admin.register(AtcTurnResponse)
class AtcTurnResponseAdmin(admin.ModelAdmin):
    """
    ATC轮次回答后台管理
    """
    list_display = [
        'id',
        'turn_short',
        'user',
        'audio_preview',
        'score_display',
        'mode_type',
        'is_timeout',
        'created_at'
    ]
    list_filter = ['mode_type', 'is_timeout', 'created_at']
    search_fields = ['user__username', 'atc_turn__scenario__title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('atc_turn', 'user', 'mode_type')
        }),
        ('回答信息', {
            'fields': ('audio_file_path', 'audio_player_display', 'score', 'is_timeout')
        }),
        ('关联模块', {
            'fields': ('modules',),
            'description': '💡 该回答所属的试题模块（可多选）'
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'audio_player_display']
    
    filter_horizontal = ['modules']
    
    def turn_short(self, obj):
        """显示轮次缩略"""
        if obj.atc_turn and obj.atc_turn.scenario:
            speaker = '👨‍✈️' if obj.atc_turn.speaker_type == 'pilot' else '🗼'
            return f'{speaker} {obj.atc_turn.scenario.title} - T{obj.atc_turn.turn_number}'
        return '-'
    turn_short.short_description = '轮次'
    
    def score_display(self, obj):
        """显示得分（带颜色）"""
        if obj.score is not None:
            score = float(obj.score)
            if score >= 80:
                color = 'green'
            elif score >= 60:
                color = 'orange'
            else:
                color = 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
                color, score
            )
        return '-'
    score_display.short_description = '得分'
    
    def audio_preview(self, obj):
        """列表页音频预览（可播放）"""
        if obj.audio_file_path:
            audio_url = obj.audio_file_path.get_file_url()
            return mark_safe(f'''
                <div style="display: flex; align-items: center; gap: 5px;">
                    <i class="fas fa-microphone" style="font-size: 16px; color: #28a745;"></i>
                    <audio controls style="height: 28px; width: 160px;" preload="none">
                        <source src="{audio_url}" type="audio/mpeg">
                    </audio>
                </div>
            ''')
        return mark_safe('<span style="color: #999;">无录音</span>')
    audio_preview.short_description = '回答音频'
    
    def audio_player_display(self, obj):
        """详情页音频播放器"""
        if obj.audio_file_path:
            audio_url = obj.audio_file_path.get_file_url()
            
            duration_display = ''
            if obj.audio_file_path.duration_ms:
                seconds = obj.audio_file_path.duration_ms / 1000
                if seconds < 60:
                    duration_display = f'{seconds:.1f}秒'
                else:
                    minutes = seconds / 60
                    duration_display = f'{minutes:.1f}分钟'
            
            return mark_safe(f'''
                <div style="padding: 15px; background: #f0fff4; border-left: 4px solid #28a745; border-radius: 4px;">
                    <div style="margin-bottom: 10px;">
                        <i class="fas fa-microphone" style="color: #28a745; font-size: 24px;"></i>
                        <strong style="margin-left: 10px; font-size: 16px;">用户回答录音</strong>
                    </div>
                    <audio controls style="width: 100%; margin: 10px 0;">
                        <source src="{audio_url}" type="audio/mpeg">
                        您的浏览器不支持音频播放。
                    </audio>
                    <div style="color: #666; font-size: 12px; margin-top: 5px;">
                        {f'<i class="fas fa-clock"></i> 时长: {duration_display}' if duration_display else ''}
                        <br>
                        <a href="{audio_url}" target="_blank" download style="color: #28a745;">
                            <i class="fas fa-download"></i> 下载录音
                        </a>
                    </div>
                </div>
            ''')
        return mark_safe('<p style="color: #999;">未上传录音</p>')
    audio_player_display.short_description = '回答音频播放器'
