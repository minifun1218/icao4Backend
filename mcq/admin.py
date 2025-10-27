"""
MCQ (听力选择题) Admin 配置
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import McqMaterial, McqQuestion, McqChoice, McqResponse


class McqChoiceInline(admin.TabularInline):
    """
    选择题选项内联编辑（自动生成A、B、C、D标签）
    """
    model = McqChoice
    extra = 4  # 默认显示4个额外的空白表单（A、B、C、D）
    max_num = 4
    fields = ['label', 'content', 'is_correct']
    ordering = ['label']
    
    def get_formset(self, request, obj=None, **kwargs):
        """自定义formset，为新选项设置默认label"""
        # 先调用父类方法获取formset类
        FormSet = super().get_formset(request, obj, **kwargs)
        
        # 保存obj引用和已有labels
        question_obj = obj
        existing_labels = set()
        if question_obj:
            existing_labels = set(question_obj.choices.values_list('label', flat=True))
        
        # 自定义formset类
        class CustomFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                # 必须先调用父类初始化
                super().__init__(*args, **kwargs)
                
                # 所有可用的label
                all_labels = ['A', 'B', 'C', 'D']
                # 已使用的label（从外部作用域获取）
                used = set(existing_labels)
                
                # 为新的空白表单分配label
                for form in self.forms:
                    # 检查是否是新表单（没有pk）
                    if not form.instance.pk:
                        # 如果label字段为空
                        if not form.instance.label and 'label' not in form.initial:
                            # 找到第一个未使用的label
                            for label in all_labels:
                                if label not in used:
                                    form.initial['label'] = label
                                    used.add(label)
                                    break
        
        return CustomFormSet


@admin.register(McqMaterial)
class McqMaterialAdmin(admin.ModelAdmin):
    """
    MCQ听力材料后台管理
    """
    list_display = [
        'id',
        'title',
        'audio_preview',
        'difficulty',
        'question_count_display',
        'module_display',
        'is_enabled',
        'display_order',
        'created_at'
    ]
    list_filter = ['difficulty', 'is_enabled', 'exam_module', 'created_at']
    search_fields = ['title', 'description', 'content']
    ordering = ['display_order', '-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'difficulty', 'display_order', 'is_enabled'),
            'description': '💡 提示：标题可留空，系统将自动使用音频文件名作为标题'
        }),
        ('音频资源', {
            'fields': ('audio_asset', 'audio_player_display')
        }),
        ('关联模块', {
            'fields': ('exam_module',),
            'description': '💡 选择该材料所属的试题模块（可多选）。注意：材料关联到模块后，材料下的所有题目都会自动关联到该模块'
        }),
        ('材料内容', {
            'fields': ('content',),
            'classes': ('collapse',),
            'description': '听力材料的文字稿（可选）'
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'audio_player_display']
    
    # 多对多字段使用水平过滤器
    filter_horizontal = ['exam_module']
    
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
                        <strong style="margin-left: 10px; font-size: 16px;">听力材料音频</strong>
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
    
    def question_count_display(self, obj):
        """显示问题数量"""
        count = obj.questions.count()
        if count > 0:
            return format_html(
                '<a href="/admin/mcq/mcqquestion/?material__id__exact={}" style="color: #17a2b8;">{} 个问题</a>',
                obj.id, count
            )
        return '0 个问题'
    question_count_display.short_description = '关联问题'
    
    def module_display(self, obj):
        """显示关联的模块"""
        modules = obj.exam_module.all()
        if modules:
            module_list = ', '.join([f'{m.title}' for m in modules[:3]])
            if modules.count() > 3:
                module_list += f' +{modules.count() - 3}个'
            return format_html(
                '<span style="color: #28a745;">{}</span>',
                module_list
            )
        return format_html('<span style="color: #999;">未关联</span>')
    module_display.short_description = '关联模块'


@admin.register(McqQuestion)
class McqQuestionAdmin(admin.ModelAdmin):
    """
    听力选择题后台管理
    """
    list_display = [
        'id',
        'material',
        'text_stem',
        'audio_preview',
        'choice_count',
        'correct_answer',

        'created_at'
    ]
    list_filter = ['material', 'created_at']
    search_fields = ['text_stem', 'material__title']
    ordering = ['-created_at']
    
    fieldsets = (
        ('关联信息', {
            'fields': ('material','text_stem','audio_asset', 'audio_player_display','created_at'),
            'description': '如果题目属于某个听力材料，请选择对应的材料'
        }),

    )
    readonly_fields = ['created_at', 'audio_player_display']
    

    inlines = [McqChoiceInline]
    

    
    def text_stem_short(self, obj):
        """显示题干缩略"""
        if obj.text_stem:
            return obj.text_stem[:50] + '...' if len(obj.text_stem) > 50 else obj.text_stem
        return '-'
    text_stem_short.short_description = '题干'
    
    def audio_preview(self, obj):
        """列表页音频预览（可播放）"""
        audio = obj.get_audio()
        if audio:
            audio_url = audio.get_file_url()
            source = '材料' if (obj.material and obj.material.audio_asset) else '题目'
            return mark_safe(f'''
                <div style="display: flex; align-items: center; gap: 5px;">
                    <i class="fas fa-file-audio" style="font-size: 16px; color: #17a2b8;" title="{source}音频"></i>
                    <audio controls style="height: 28px; width: 160px;" preload="none">
                        <source src="{audio_url}" type="audio/mpeg">
                    </audio>
                </div>
            ''')
        return mark_safe('<span style="color: #999;">无音频</span>')
    audio_preview.short_description = '音频播放'
    
    def audio_player_display(self, obj):
        """详情页音频播放器（显示来源）"""
        audio = obj.get_audio()
        if audio:
            audio_url = audio.get_file_url()
            is_from_material = obj.material and obj.material.audio_asset
            source_text = '来源：关联材料' if is_from_material else '来源：题目独立音频'
            source_color = '#28a745' if is_from_material else '#17a2b8'
            
            duration_display = ''
            if audio.duration_ms:
                seconds = audio.duration_ms / 1000
                if seconds < 60:
                    duration_display = f'{seconds:.1f}秒'
                else:
                    minutes = seconds / 60
                    duration_display = f'{minutes:.1f}分钟'
            
            return mark_safe(f'''
                <div style="padding: 15px; background: #f0f8ff; border-left: 4px solid {source_color}; border-radius: 4px;">
                    <div style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <i class="fas fa-volume-up" style="color: {source_color}; font-size: 24px;"></i>
                            <strong style="margin-left: 10px; font-size: 16px;">题目音频</strong>
                        </div>
                        <span style="color: {source_color}; font-size: 12px;">
                            <i class="fas fa-info-circle"></i> {source_text}
                        </span>
                    </div>
                    <audio controls style="width: 100%; margin: 10px 0;">
                        <source src="{audio_url}" type="audio/mpeg">
                        您的浏览器不支持音频播放。
                    </audio>
                    <div style="color: #666; font-size: 12px; margin-top: 5px;">
                        {f'<i class="fas fa-clock"></i> 时长: {duration_display}' if duration_display else ''}
                        {f'<span style="margin-left: 15px;"><i class="fas fa-link"></i> 材料: {obj.material.title}</span>' if is_from_material else ''}
                        <br>
                        <a href="{audio_url}" target="_blank" download style="color: {source_color};">
                            <i class="fas fa-download"></i> 下载音频
                        </a>
                    </div>
                </div>
            ''')
        return mark_safe('''
            <div style="padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                <i class="fas fa-exclamation-triangle" style="color: #856404;"></i>
                <span style="color: #856404; margin-left: 5px;">
                    未设置音频（请关联材料或上传独立音频）
                </span>
            </div>
        ''')
    audio_player_display.short_description = '音频播放器'
    
    def choice_count(self, obj):
        """显示选项数量"""
        return obj.choices.count()
    choice_count.short_description = '选项数量'
    
    def correct_answer(self, obj):
        """显示正确答案"""
        correct_choice = obj.choices.filter(is_correct=True).first()
        if correct_choice:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                correct_choice.label
            )
        return format_html('<span style="color: red;">未设置</span>')
    correct_answer.short_description = '正确答案'


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
        'is_correct_display',
        'module_display',
        'mode_type',
        'is_timeout',
        'answered_at',
        'created_at'
    ]
    list_filter = ['is_correct', 'mode_type', 'is_timeout', 'module', 'answered_at', 'created_at']
    search_fields = ['user__nickname', 'user__openid', 'question__text_stem']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('question', 'user')
        }),
        ('回答信息', {
            'fields': ('selected_choice', 'is_correct', 'mode_type', 'is_timeout', 'answered_at')
        }),
        ('关联模块', {
            'fields': ('module',),
            'description': '该答题记录所属的模块（可多选）'
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'answered_at']
    
    filter_horizontal = ['module']
    
    def is_correct_display(self, obj):
        """显示是否正确（带颜色）"""
        if obj.is_correct is None:
            return format_html('<span style="color: #999;">未判分</span>')
        elif obj.is_correct:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ 正确</span>')
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">✗ 错误</span>')
    is_correct_display.short_description = '是否正确'
    
    def module_display(self, obj):
        """显示关联的模块"""
        modules = obj.module.all()
        if modules:
            module_list = ', '.join([f'{m.title}' for m in modules[:2]])
            if modules.count() > 2:
                module_list += f' +{modules.count() - 2}个'
            return format_html(
                '<span style="color: #007bff;">{}</span>',
                module_list
            )
        return format_html('<span style="color: #999;">未关联</span>')
    module_display.short_description = '关联模块'
