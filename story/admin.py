"""
Story (故事复述) Admin 配置
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import RetellItem, RetellResponse


@admin.register(RetellItem)
class RetellItemAdmin(admin.ModelAdmin):
    """
    复述题目后台管理
    """
    list_display = [
        'id',
        'title',
        'audio_preview',
        'response_count',
        'module_display',
        'created_at'
    ]
    list_filter = ['created_at', 'exam_modules']
    search_fields = ['title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title',),
            'description': '💡 提示：题目标题'
        }),
        ('音频资源', {
            'fields': ('audio_asset', 'audio_player_display')
        }),
        ('关联模块', {
            'fields': ('exam_modules',),
            'description': '💡 选择该题目所属的试题模块（可多选）'
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'audio_player_display']
    
    filter_horizontal = ['exam_modules']
    
    def module_display(self, obj):
        """显示关联的模块"""
        modules = obj.exam_modules.all()
        if modules:
            return ', '.join([f'{m.title}' for m in modules[:3]])
        return '-'
    module_display.short_description = '关联模块'
    
    def audio_preview(self, obj):
        """列表页音频预览（可播放）"""
        if obj.audio_asset:
            audio_url = obj.audio_asset.get_file_url()
            return mark_safe(f'''
                <div style="display: flex; align-items: center; gap: 5px;">
                    <i class="fas fa-file-audio" style="font-size: 20px; color: #17a2b8;"></i>
                    <audio controls style="height: 30px; width: 180px;" preload="none">
                        <source src="{audio_url}" type="audio/mpeg">
                    </audio>
                </div>
            ''')
        return '-'
    audio_preview.short_description = '音频播放'
    
    def audio_player_display(self, obj):
        """详情页音频播放器"""
        if obj.audio_asset:
            audio_url = obj.audio_asset.get_file_url()
            duration_display = ''
            if obj.audio_asset.duration_ms:
                seconds = obj.audio_asset.duration_ms / 1000
                if seconds < 60:
                    duration_display = f'{seconds:.1f}秒'
                else:
                    minutes = seconds / 60
                    duration_display = f'{minutes:.1f}分钟'
            
            return mark_safe(f'''
                <div style="padding: 15px; background: #f0f8ff; border-left: 4px solid #17a2b8; border-radius: 4px;">
                    <div style="margin-bottom: 10px;">
                        <i class="fas fa-volume-up" style="color: #17a2b8; font-size: 24px;"></i>
                        <strong style="margin-left: 10px; font-size: 16px;">故事复述音频</strong>
                    </div>
                    <audio controls style="width: 100%; margin: 10px 0;">
                        <source src="{audio_url}" type="audio/mpeg">
                        您的浏览器不支持音频播放。
                    </audio>
                    <div style="color: #666; font-size: 12px; margin-top: 5px;">
                        {f'<i class="fas fa-clock"></i> 时长: {duration_display}' if duration_display else ''}
                        <br>
                        <a href="{audio_url}" target="_blank" download style="color: #17a2b8;">
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
                '<a href="/admin/story/retellresponse/?retell_item__id__exact={}" style="color: #17a2b8;">{} 个回答</a>',
                obj.id, count
            )
        return '0 个回答'
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
        'audio_preview',
        'score_display',
        'mode_type',
        'is_timeout',
        'answered_at',
        'created_at'
    ]
    list_filter = ['mode_type', 'is_timeout', 'answered_at', 'created_at']
    search_fields = ['user__username', 'retell_item__title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('retell_item', 'user', 'mode_type')
        }),
        ('回答信息', {
            'fields': ('answer_audio', 'audio_player_display', 'score', 'is_timeout', 'answered_at')
        }),
        ('关联模块', {
            'fields': ('modules',),
            'description': '💡 该回答所属的试题模块（可多选）'
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'answered_at', 'audio_player_display']
    
    filter_horizontal = ['modules']
    
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
        if obj.answer_audio:
            audio_url = obj.answer_audio.get_file_url()
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
        if obj.answer_audio:
            audio_url = obj.answer_audio.get_file_url()
            
            duration_display = ''
            if obj.answer_audio.duration_ms:
                seconds = obj.answer_audio.duration_ms / 1000
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
