"""
LSA (听力简答) Admin 配置
"""
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import LsaDialog, LsaQuestion, LsaResponse


class LsaDialogAdminForm(forms.ModelForm):
    """
    听力简答对话后台表单
    添加自定义字段来管理问题关联
    """
    questions = forms.ModelMultipleChoiceField(
        queryset=LsaQuestion.objects.all().order_by('display_order', 'id'),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('问题', False),
        label='关联问题',
        help_text='选择该对话关联的问题（可多选）'
    )
    
    class Meta:
        model = LsaDialog
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # 如果是编辑现有对话，预填充已关联的问题
            self.fields['questions'].initial = self.instance.lsa_questions.all()
    
    # 保存逻辑在 LsaDialogAdmin.save_model 中处理


# 由于 LsaQuestion 的 dialog 改为 ManyToManyField，不再支持内联编辑
# class LsaQuestionInline(admin.TabularInline):
#     """
#     LSA问题内联编辑
#     """
#     model = LsaQuestion
#     extra = 1
#     fields = ['question_text', 'question_type', 'display_order', 'correct_answer', 'is_active']
#     ordering = ['display_order']


@admin.register(LsaDialog)
class LsaDialogAdmin(admin.ModelAdmin):
    """
    听力简答对话后台管理
    """
    form = LsaDialogAdminForm
    
    list_display = [
        'id',
        'title',
        'audio_preview',
        'is_active',
        'linked_questions_count',
        'module_display',
        'created_at'
    ]
    list_filter = ['is_active', 'created_at', 'exam_module']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'audio_asset', 'audio_player_display',
                        'is_active', 'created_at', 'updated_at'),
            'description': '💡 提示：对话的基本信息'
        }),

        ('关联模块', {
            'fields': ('exam_module',),
            'description': '💡 选择该对话所属的试题模块（可多选，可不选）'
        }),
        
        ('关联问题', {
            'fields': ('questions', 'current_questions_display'),
            'description': '💡 选择该对话关联的问题（可多选）- 通过多选框选择问题',
            'classes': ('collapse',)
        }),

    )
    
    readonly_fields = ['created_at', 'updated_at', 'audio_player_display', 'current_questions_display']
    
    filter_horizontal = ['exam_module']
    
    # 由于 dialog 改为多对多关系，不再使用内联编辑
    # inlines = [LsaQuestionInline]
    
    def save_model(self, request, obj, form, change):
        """保存模型时确保问题关联被正确处理"""
        super().save_model(request, obj, form, change)
        
        # 获取选择的问题
        if 'questions' in form.cleaned_data:
            selected_questions = list(form.cleaned_data['questions'])

            # 获取当前已关联的问题
            current_questions = list(obj.lsa_questions.all())

            # 转换为集合方便比较
            current_ids = set(q.id for q in current_questions)
            selected_ids = set(q.id for q in selected_questions)
            
            # 需要添加的问题
            to_add = [q for q in selected_questions if q.id not in current_ids]
            # 需要移除的问题
            to_remove = [q for q in current_questions if q.id not in selected_ids]
            
            # 添加新关联
            for question in to_add:
                question.dialog.add(obj)
            
            # 移除旧关联
            for question in to_remove:
                question.dialog.remove(obj)
            
            # 验证保存结果
            final_questions = list(obj.lsa_questions.all())
        else:
            print("[DEBUG] 表单中没有 'questions' 字段")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """自定义多对多字段的查询集，只显示 LISTENING_SA 类型的考试模块"""
        if db_field.name == "exam_module":
            kwargs["queryset"] = db_field.related_model.objects.filter(
                module_type='LISTENING_SA',
                is_activate=True
            ).order_by('display_order', 'created_at')
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def module_display(self, obj):
        """显示关联的模块（仅显示标题，不显示计数）"""
        modules = obj.exam_module.filter(module_type='LISTENING_SA')
        if modules.exists():
            return ', '.join([m.title or m.get_module_type_display() for m in modules[:3]])
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
    
    def linked_questions_count(self, obj):
        """显示与此对话关联的问题数量（通过问题的dialog字段）"""
        # 由于 dialog 改为多对多，使用 lsa_questions 作为反向关系名
        count = obj.lsa_questions.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<span style="color: #17a2b8; font-weight: bold;">{} 个</span>',
                count
            )
        return '0 个'
    linked_questions_count.short_description = '关联问题'
    
    def current_questions_display(self, obj):
        """显示当前已关联的问题列表"""
        if not obj.pk:
            return mark_safe('<p style="color: #999;">保存后可查看关联的问题</p>')
        
        questions = obj.lsa_questions.all().order_by('display_order', 'id')
        if questions.exists():
            items = []
            for q in questions:
                items.append(f'''
                    <div style="padding: 5px; border-bottom: 1px solid #eee;">
                        <strong>Q{q.id}</strong>: {q.question_text[:80]}{'...' if len(q.question_text) > 80 else ''}
                        <span style="color: #666; font-size: 12px;">(顺序: {q.display_order or '-'})</span>
                    </div>
                ''')
            return mark_safe(f'''
                <div style="padding: 10px; background: #f9f9f9; border: 1px solid #ddd; border-radius: 4px; max-height: 300px; overflow-y: auto;">
                    <div style="margin-bottom: 10px; color: #17a2b8;">
                        <i class="fas fa-list"></i> <strong>共 {questions.count()} 个问题</strong>
                    </div>
                    {''.join(items)}
                </div>
            ''')
        return mark_safe('<p style="color: #999;">暂无关联问题</p>')
    current_questions_display.short_description = '当前已关联的问题'


@admin.register(LsaQuestion)
class LsaQuestionAdmin(admin.ModelAdmin):
    """
    听力简答问题后台管理
    """
    list_display = [
        'id',
        'question_text_short',
        'audio_preview',
        'display_order',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['question_text']
    ordering = ['display_order', '-created_at']
    
    fieldsets = (
        ('题目信息', {
            'fields': (
                'question_text',
                'question_audio',
                'audio_player_display',
                'display_order',
                'is_active',
                'created_at',
                'updated_at'
            ),
            'description': '💡 填写题目文本并上传问题音频'
        }),
       
    )
    
    readonly_fields = ['created_at', 'updated_at', 'audio_player_display']
    
    filter_horizontal = ['dialog']
    
    def question_text_short(self, obj):
        """显示题干缩略"""
        if obj.question_text:
            return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
        return '-'
    question_text_short.short_description = '题干'
    
    def audio_preview(self, obj):
        """列表页音频预览（可播放）"""
        if obj.question_audio:
            audio_url = obj.question_audio.get_file_url()
            return mark_safe(f'''
                <div style="display: flex; align-items: center; gap: 5px;">
                    <i class="fas fa-file-audio" style="font-size: 16px; color: #17a2b8;"></i>
                    <audio controls style="height: 28px; width: 160px;" preload="none">
                        <source src="{audio_url}" type="audio/mpeg">
                    </audio>
                </div>
            ''')
        return mark_safe('<span style="color: #999;">无音频</span>')
    audio_preview.short_description = '问题音频'
    
    def audio_player_display(self, obj):
        """详情页音频播放器"""
        if obj.question_audio:
            audio_url = obj.question_audio.get_file_url()
            
            duration_display = ''
            if obj.question_audio.duration_ms:
                seconds = obj.question_audio.duration_ms / 1000
                if seconds < 60:
                    duration_display = f'{seconds:.1f}秒'
                else:
                    minutes = seconds / 60
                    duration_display = f'{minutes:.1f}分钟'
            
            return mark_safe(f'''
                <div style="padding: 15px; background: #f0f8ff; border-left: 4px solid #17a2b8; border-radius: 4px;">
                    <div style="margin-bottom: 10px;">
                        <i class="fas fa-volume-up" style="color: #17a2b8; font-size: 24px;"></i>
                        <strong style="margin-left: 10px; font-size: 16px;">问题音频</strong>
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
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """自定义多对多字段的查询集，只显示 LISTENING_SA 类型的考试模块"""
        if db_field.name == "modules":
            kwargs["queryset"] = db_field.related_model.objects.filter(
                module_type='LISTENING_SA',
                is_activate=True
            ).order_by('display_order', 'created_at')
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
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
