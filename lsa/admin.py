"""
LSA (听力简答) Admin 配置
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
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
        'audio_preview',
        'display_order',
        'is_active',
        'question_count',
        'module_display',
        'created_at'
    ]
    list_filter = ['is_active', 'created_at', 'exam_module']
    search_fields = ['title', 'description']
    ordering = ['display_order', '-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'display_order'),
            'description': '💡 提示：对话的基本信息'
        }),
        ('音频资源', {
            'fields': ('audio_asset', 'audio_player_display')
        }),
        ('关联模块', {
            'fields': ('exam_module',),
            'description': '💡 选择该对话所属的试题模块（可多选）'
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
    
    filter_horizontal = ['exam_module']
    
    inlines = [LsaQuestionInline]
    
    def module_display(self, obj):
        """显示关联的模块"""
        modules = obj.exam_module.all()
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
                        <strong style="margin-left: 10px; font-size: 16px;">对话音频</strong>
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
    
    def question_count(self, obj):
        """显示问题数量"""
        count = obj.questions.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<a href="/admin/lsa/lsaquestion/?dialog__id__exact={}" style="color: #17a2b8;">{} 个问题</a>',
                obj.id, count
            )
        return '0 个问题'
    question_count.short_description = '问题数量'


@admin.register(LsaQuestion)
class LsaQuestionAdmin(admin.ModelAdmin):
    """
    听力简答问题后台管理
    """
    list_display = [
        'id',
        'dialog',
        'question_text_short',
        'question_type',
        'correct_answer_display',
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
            'fields': ('option_a', 'option_b', 'option_c', 'option_d'),
            'description': '💡 如果是选择题，请填写选项'
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
    
    def question_text_short(self, obj):
        """显示题干缩略"""
        if obj.question_text:
            return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
        return '-'
    question_text_short.short_description = '题干'
    
    def correct_answer_display(self, obj):
        """显示正确答案"""
        if obj.correct_answer:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                obj.correct_answer
            )
        return format_html('<span style="color: #999;">未设置</span>')
    correct_answer_display.short_description = '正确答案'


@admin.register(LsaResponse)
class LsaResponseAdmin(admin.ModelAdmin):
    """
    听力简答回答后台管理
    """
    list_display = [
        'id',
        'question_short',
        'user',
        'audio_preview',
        'mode_type',
        'is_timeout',
        'answered_at',
        'created_at'
    ]
    list_filter = ['mode_type', 'is_timeout', 'answered_at', 'created_at']
    search_fields = ['user__username', 'question__question_text']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('question', 'user', 'mode_type')
        }),
        ('回答信息', {
            'fields': ('answer_audio', 'audio_player_display', 'is_timeout', 'answered_at')
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
    
    def question_short(self, obj):
        """显示题目缩略"""
        if obj.question:
            return obj.question.question_text[:30] + '...' if len(obj.question.question_text) > 30 else obj.question.question_text
        return '-'
    question_short.short_description = '题目'
    
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
