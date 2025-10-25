"""
Exam Admin 配置
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
from .models import ExamPaper, ExamModule


class ExamModuleInline(admin.TabularInline):
    """
    考试模块内联编辑
    """
    model = ExamModule.exam_paper.through
    extra = 1
    verbose_name = '试题模块'
    verbose_name_plural = '试题模块'


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
            'fields': ('total_duration_min',),
            'description': '试卷总时长，单位：分钟'
        }),
        ('关联模块', {
            'fields': ('modules_display',),
            'classes': ('wide',),
            'description': '此试卷包含的所有模块'
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'modules_display']
    
    inlines = [ExamModuleInline]
    
    def module_count(self, obj):
        """显示模块数量"""
        count = obj.exammodule_set.filter(is_activate=True).count()
        if count > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{} 个模块</span>',
                count
            )
        return format_html('<span style="color: #dc3545;">0 个模块</span>')
    module_count.short_description = '模块数量'
    
    def modules_display(self, obj):
        """显示关联的模块列表"""
        if not obj.pk:
            return mark_safe('<p style="color: #999;">请先保存试卷，然后即可添加模块</p>')
        
        modules = obj.exammodule_set.filter(is_activate=True).order_by('display_order')
        count = modules.count()
        
        html = f'''
        <div style="padding: 15px; background: #f8f9fa; border-left: 4px solid #28a745; border-radius: 4px;">
            <div style="margin-bottom: 10px;">
                <strong style="font-size: 14px;">📚 试卷模块</strong>
                <span style="margin-left: 10px; color: #666;">共 {count} 个模块</span>
            </div>
        '''
        
        if count > 0:
            html += '<div style="margin: 10px 0; max-height: 300px; overflow-y: auto;">'
            html += '<table style="width: 100%; border-collapse: collapse;">'
            html += '<thead><tr style="background: #e9ecef;">'
            html += '<th style="padding: 8px; text-align: left;">顺序</th>'
            html += '<th style="padding: 8px; text-align: left;">标题</th>'
            html += '<th style="padding: 8px; text-align: left;">类型</th>'
            html += '<th style="padding: 8px; text-align: center;">题目数</th>'
            html += '<th style="padding: 8px; text-align: center;">时长</th>'
            html += '<th style="padding: 8px; text-align: center;">操作</th>'
            html += '</tr></thead><tbody>'
            
            for module in modules:
                # 计算题目数量
                question_count = 0
                if module.module_type == 'LISTENING_MCQ':
                    question_count = module.module_mcq.count()
                elif module.module_type == 'STORY_RETELL':
                    question_count = module.retell_items.count()
                elif module.module_type == 'LISTENING_SA':
                    question_count = module.module_lsa.count()
                elif module.module_type == 'OPI':
                    question_count = module.opi_topic.count()
                elif module.module_type == 'ATC_SIM':
                    question_count = module.atc_scenarios.count()
                
                # 格式化时长
                duration_text = '未设置'
                if module.duration:
                    seconds = module.duration / 1000
                    if seconds < 60:
                        duration_text = f'{seconds:.0f}秒'
                    else:
                        minutes = seconds / 60
                        duration_text = f'{minutes:.1f}分钟'
                
                html += f'''
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px;">{module.display_order or 0}</td>
                    <td style="padding: 8px;">{module.title or '-'}</td>
                    <td style="padding: 8px;">{module.get_module_type_display()}</td>
                    <td style="padding: 8px; text-align: center;">{question_count} 道</td>
                    <td style="padding: 8px; text-align: center;">{duration_text}</td>
                    <td style="padding: 8px; text-align: center;">
                        <a href="/admin/exam/exammodule/{module.id}/change/" target="_blank" style="color: #007bff;">
                            编辑
                        </a>
                    </td>
                </tr>
                '''
            
            html += '</tbody></table></div>'
        
        # 添加管理按钮
        html += f'''
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <a href="/admin/exam/exammodule/?exam_paper__id__exact={obj.id}" 
                   target="_blank"
                   style="display: inline-block; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">
                    <i class="fas fa-list"></i> 查看所有关联模块
                </a>
                <a href="/admin/exam/exammodule/add/" 
                   target="_blank"
                   style="display: inline-block; padding: 8px 16px; background: #28a745; color: white; text-decoration: none; border-radius: 4px;">
                    <i class="fas fa-plus"></i> 添加新模块
                </a>
            </div>
        </div>
        '''
        
        return mark_safe(html)
    
    modules_display.short_description = '包含的模块'


class ExamModuleAdminForm(forms.ModelForm):
    """自定义表单，处理反向多对多关系"""
    
    mcq_materials = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('听力材料', False),
        label='听力材料',
        help_text='选择要包含在此模块中的听力材料（会自动关联材料下的所有题目）'
    )
    
    retell_items = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('故事复述题', False),
        label='故事复述题',
        help_text='选择要包含在此模块中的故事复述题'
    )
    
    lsa_dialogs = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('听力简答对话', False),
        label='听力简答对话',
        help_text='选择要包含在此模块中的听力简答对话'
    )
    
    opi_topics = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('OPI话题', False),
        label='OPI话题',
        help_text='选择要包含在此模块中的OPI话题'
    )
    
    class Meta:
        model = ExamModule
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 导入模型
        from mcq.models import McqMaterial, McqQuestion
        from story.models import RetellItem
        from lsa.models import LsaDialog
        from opi.models import OpiTopic
        
        # 设置 queryset
        self.fields['mcq_materials'].queryset = McqMaterial.objects.filter(is_enabled=True).order_by('display_order', 'title')
        self.fields['retell_items'].queryset = RetellItem.objects.all()
        self.fields['lsa_dialogs'].queryset = LsaDialog.objects.filter(is_active=True).order_by('display_order', 'title')
        self.fields['opi_topics'].queryset = OpiTopic.objects.all().order_by('order', 'title')
        
        # 如果是编辑现有对象，设置初始值
        if self.instance and self.instance.pk:
            # MCQ: 获取当前模块关联的所有题目的材料（去重）
            mcq_questions = self.instance.module_mcq.all()
            mcq_material_ids = mcq_questions.filter(material__isnull=False).values_list('material_id', flat=True).distinct()
            self.fields['mcq_materials'].initial = McqMaterial.objects.filter(id__in=mcq_material_ids)
            
            self.fields['retell_items'].initial = self.instance.retell_items.all()
            self.fields['lsa_dialogs'].initial = self.instance.module_lsa.all()
            self.fields['opi_topics'].initial = self.instance.opi_topic.all()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            self.save_m2m()
        
        # 保存反向多对多关系
        if self.instance.pk:
            # 更新 MCQ 听力材料：将选中材料下的所有题目关联到模块
            if 'mcq_materials' in self.cleaned_data:
                from mcq.models import McqQuestion
                
                selected_materials = self.cleaned_data['mcq_materials']
                
                # 获取所有选中材料下的题目
                questions_to_add = []
                for material in selected_materials:
                    questions_to_add.extend(material.questions.all())
                
                # 清除当前模块下所有通过材料关联的题目
                # 保留那些没有关联材料的独立题目
                current_questions = instance.module_mcq.all()
                standalone_questions = current_questions.filter(material__isnull=True)
                
                # 设置新的题目列表：独立题目 + 选中材料的题目
                all_questions = list(standalone_questions) + questions_to_add
                instance.module_mcq.set(all_questions)
            
            # 更新故事复述题
            if 'retell_items' in self.cleaned_data:
                instance.retell_items.set(self.cleaned_data['retell_items'])
            
            # 更新听力简答题
            if 'lsa_dialogs' in self.cleaned_data:
                instance.module_lsa.set(self.cleaned_data['lsa_dialogs'])
            
            # 更新 OPI 话题
            if 'opi_topics' in self.cleaned_data:
                instance.opi_topic.set(self.cleaned_data['opi_topics'])
        
        return instance


@admin.register(ExamModule)
class ExamModuleAdmin(admin.ModelAdmin):
    """
    考试模块后台管理
    """
    form = ExamModuleAdminForm
    
    list_display = [
        'id',
        'title',
        'get_module_type_display',
        'question_count',
        'display_order',
        'score',
        'duration_display',
        'is_activate',
        'created_at'
    ]
    list_filter = ['is_activate', 'module_type', 'created_at']
    search_fields = ['title', 'module_type']
    ordering = ['display_order', '-created_at']
    
    def get_fieldsets(self, request, obj=None):
        """动态生成fieldsets，根据模块类型显示不同的关联试题字段"""
        base_fieldsets = [
            ('基本信息', {
                'fields': ('title', 'module_type', 'display_order', 'score', 'duration', 'is_activate', 'created_at'),
                'description': '提示：选择模块类型并保存后，下方会出现对应的试题选择器'
            }),
            ('关联试卷', {
                'fields': ('exam_paper',),
                'description': '可选：将此模块关联到一个或多个试卷（使用下方的选择器，可多选）'
            }),
        ]
        
        # 如果对象已存在，根据模块类型添加对应的试题选择字段
        if obj and obj.pk:
            module_type = obj.module_type
            
            if module_type == 'LISTENING_MCQ':
                base_fieldsets.append(
                    ('选择听力材料', {
                        'fields': ('mcq_materials',),
                        'classes': ('wide',),
                        'description': '从题库中选择听力材料（一段材料包含多道题目，选择材料后会自动关联该材料下的所有题目）'
                    })
                )
            elif module_type == 'STORY_RETELL':
                base_fieldsets.append(
                    ('选择故事复述题', {
                        'fields': ('retell_items',),
                        'classes': ('wide',),
                        'description': '从题库中选择要包含在此模块中的故事复述题（可多选）'
                    })
                )
            elif module_type == 'LISTENING_SA':
                base_fieldsets.append(
                    ('选择听力简答题', {
                        'fields': ('lsa_dialogs',),
                        'classes': ('wide',),
                        'description': '从题库中选择要包含在此模块中的听力简答对话（可多选）'
                    })
                )
            elif module_type == 'OPI':
                base_fieldsets.append(
                    ('选择OPI话题', {
                        'fields': ('opi_topics',),
                        'classes': ('wide',),
                        'description': '从题库中选择要包含在此模块中的OPI话题（可多选）'
                    })
                )
            elif module_type == 'ATC_SIM':
                base_fieldsets.append(
                    ('ATC场景管理', {
                        'fields': ('atc_info_display',),
                        'classes': ('wide',),
                        'description': 'ATC场景使用一对多关系，请在ATC场景管理中选择此模块'
                    })
                )
            
            # 添加已关联题目的详细统计
            base_fieldsets.append(
                ('已关联题目详情', {
                    'fields': ('questions_display',),
                    'classes': ('wide', 'collapse'),
                    'description': '查看当前模块已关联的所有题目详细信息'
                })
            )
        else:
            # 新建模块时的提示
            base_fieldsets.append(
                ('关联试题', {
                    'fields': (),
                    'description': '请先填写基本信息并保存，然后即可选择关联的试题'
                })
            )
        

        
        return base_fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        """动态设置只读字段"""
        readonly = ['created_at', 'questions_display']
        
        # ATC场景是一对多关系，使用只读显示
        if obj and obj.module_type == 'ATC_SIM':
            readonly.append('atc_info_display')
        
        return readonly
    
    
    def atc_info_display(self, obj):
        """ATC场景信息显示"""
        scenarios = obj.atc_scenarios.all()
        count = scenarios.count()
        
        html = f'''
        <div style="padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
            <p style="margin: 0 0 10px 0;"><strong>⚠️ ATC场景使用一对多关系</strong></p>
            <p style="margin: 0 0 10px 0;">当前已关联 <strong>{count}</strong> 个ATC场景</p>
        '''
        
        if count > 0:
            html += '<ul style="margin: 10px 0; padding-left: 20px;">'
            for scenario in scenarios[:10]:
                html += f'<li><a href="/admin/atc/atcscenario/{scenario.id}/change/" target="_blank">{scenario.title}</a> (ID: {scenario.id})</li>'
            if count > 10:
                html += f'<li style="color: #666;">... 还有 {count - 10} 个场景</li>'
            html += '</ul>'
        
        html += '''
            <div style="margin-top: 15px;">
                <a href="/admin/atc/atcscenario/add/" target="_blank" 
                   style="display: inline-block; padding: 8px 16px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px;">
                    ➕ 创建新ATC场景
                </a>
                <a href="/admin/atc/atcscenario/" target="_blank" 
                   style="display: inline-block; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">
                    📋 管理所有ATC场景
                </a>
            </div>
            <p style="margin: 15px 0 0 0; color: #856404; font-size: 12px;">
                💡 在创建或编辑ATC场景时，选择"关联模块"字段为当前模块即可将场景添加到此模块
            </p>
        </div>
        '''
        
        return mark_safe(html)
    atc_info_display.short_description = 'ATC场景'
    
    filter_horizontal = ['exam_paper']
    
    def get_module_type_display(self, obj):
        """显示模块类型"""
        return obj.get_module_type_display()
    get_module_type_display.short_description = '模块类型'
    
    def duration_display(self, obj):
        """显示时长（转换为易读格式）"""
        if obj.duration is not None and obj.duration > 0:
            seconds = obj.duration / 1000
            if seconds < 60:
                return f'{seconds:.0f}秒'
            else:
                minutes = seconds / 60
                return f'{minutes:.1f}分钟'
        return format_html('<span style="color: #999;">未设置</span>')
    duration_display.short_description = '时长'
    
    def question_count(self, obj):
        """显示关联的题目数量"""
        count = 0
        module_type = obj.module_type
        
        if module_type == 'LISTENING_MCQ':
            count = obj.module_mcq.count()
        elif module_type == 'STORY_RETELL':
            count = obj.retell_items.count()
        elif module_type == 'LISTENING_SA':
            count = obj.module_lsa.count()
        elif module_type == 'OPI':
            count = obj.opi_topic.count()
        elif module_type == 'ATC_SIM':
            count = obj.atc_scenarios.count()
        
        if count > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{} 道题</span>',
                count
            )
        return format_html('<span style="color: #dc3545;">0 道题</span>')
    question_count.short_description = '关联题目数'
    
    def questions_display(self, obj):
        """根据模块类型显示关联的题目管理链接"""
        if not obj.pk:
            return mark_safe('<p style="color: #999;">请先保存模块，然后即可关联试题</p>')
        
        module_type = obj.module_type
        
        # 根据不同的模块类型，提供不同的管理链接
        if module_type == 'LISTENING_MCQ':
            # MCQ 显示听力材料
            return self._render_mcq_materials(obj)
        elif module_type == 'STORY_RETELL':
            return self._render_question_links(
                obj,
                'story',
                'retellitem',
                obj.retell_items.all(),
                'retell_items',
                '故事复述题',
                'exam_modules__id__exact'
            )
        elif module_type == 'LISTENING_SA':
            return self._render_question_links(
                obj,
                'lsa',
                'lsadialog',
                obj.module_lsa.all(),
                'module_lsa',
                '听力简答题',
                'exam_module__id__exact'
            )
        elif module_type == 'OPI':
            return self._render_question_links(
                obj,
                'opi',
                'opitopic',
                obj.opi_topic.all(),
                'opi_topic',
                'OPI话题',
                'exam_module__id__exact'
            )
        elif module_type == 'ATC_SIM':
            return self._render_atc_links(obj)
        else:
            return mark_safe('<p style="color: #999;">未知的模块类型</p>')
    
    def _render_mcq_materials(self, obj):
        """渲染MCQ听力材料列表"""
        from mcq.models import McqMaterial
        
        # 获取当前模块关联的所有题目
        mcq_questions = obj.module_mcq.all()
        # 获取这些题目关联的材料（去重）
        material_ids = mcq_questions.filter(material__isnull=False).values_list('material_id', flat=True).distinct()
        materials = McqMaterial.objects.filter(id__in=material_ids).order_by('display_order', 'title')
        
        count = materials.count()
        total_questions = mcq_questions.count()
        
        html = f'''
        <div style="padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff; border-radius: 4px;">
            <div style="margin-bottom: 10px;">
                <strong style="font-size: 14px;">📝 听力材料</strong>
                <span style="margin-left: 10px; color: #666;">共 {count} 段材料，包含 {total_questions} 道题</span>
            </div>
        '''
        
        if count > 0:
            html += '<div style="margin: 10px 0; max-height: 300px; overflow-y: auto;">'
            html += '<table style="width: 100%; border-collapse: collapse;">'
            html += '<thead><tr style="background: #e9ecef;">'
            html += '<th style="padding: 8px; text-align: left;">ID</th>'
            html += '<th style="padding: 8px; text-align: left;">材料标题</th>'
            html += '<th style="padding: 8px; text-align: center;">难度</th>'
            html += '<th style="padding: 8px; text-align: center;">题目数</th>'
            html += '<th style="padding: 8px; text-align: center;">音频</th>'
            html += '<th style="padding: 8px; text-align: center;">创建时间</th>'
            html += '<th style="padding: 8px; text-align: center;">操作</th>'
            html += '</tr></thead><tbody>'
            
            for material in materials[:20]:
                question_count = material.questions.count()
                difficulty_map = {'easy': '简单', 'medium': '中等', 'hard': '困难'}
                difficulty = difficulty_map.get(material.difficulty, material.difficulty)
                has_audio = '✓' if material.audio_asset else '-'
                audio_color = '#28a745' if material.audio_asset else '#999'
                created_time = material.created_at.strftime('%Y-%m-%d')
                
                html += f'''
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px;">{material.id}</td>
                    <td style="padding: 8px;">{material.title}</td>
                    <td style="padding: 8px; text-align: center;">{difficulty}</td>
                    <td style="padding: 8px; text-align: center;">{question_count}</td>
                    <td style="padding: 8px; text-align: center;"><span style="color: {audio_color};">{has_audio}</span></td>
                    <td style="padding: 8px; text-align: center; color: #666; font-size: 12px;">{created_time}</td>
                    <td style="padding: 8px; text-align: center;">
                        <a href="/admin/mcq/mcqmaterial/{material.id}/change/" target="_blank" style="color: #007bff;">
                            编辑
                        </a>
                    </td>
                </tr>
                '''
            
            if count > 20:
                html += f'<tr><td colspan="7" style="padding: 8px; text-align: center; color: #666;">还有 {count - 20} 段材料...</td></tr>'
            
            html += '</tbody></table></div>'
        
        # 添加管理按钮
        html += f'''
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <a href="/admin/mcq/mcqmaterial/" 
                   target="_blank"
                   style="display: inline-block; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">
                    <i class="fas fa-list"></i> 查看所有听力材料
                </a>
                <a href="/admin/mcq/mcqmaterial/add/" 
                   target="_blank"
                   style="display: inline-block; padding: 8px 16px; background: #28a745; color: white; text-decoration: none; border-radius: 4px;">
                    <i class="fas fa-plus"></i> 添加新材料
                </a>
            </div>
        </div>
        '''
        
        return mark_safe(html)
    
    def _render_question_links(self, obj, app_name, model_name, questions, relation_name, display_name, filter_param):
        """渲染题目列表和管理链接"""
        count = questions.count()
        
        html = f'''
        <div style="padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff; border-radius: 4px;">
            <div style="margin-bottom: 10px;">
                <strong style="font-size: 14px;">📝 {display_name}</strong>
                <span style="margin-left: 10px; color: #666;">共 {count} 道题</span>
            </div>
        '''
        
        if count > 0:
            html += '<div style="margin: 10px 0; max-height: 300px; overflow-y: auto;">'
            html += '<table style="width: 100%; border-collapse: collapse;">'
            html += '<thead><tr style="background: #e9ecef;">'
            html += '<th style="padding: 8px; text-align: left;">ID</th>'
            html += '<th style="padding: 8px; text-align: left;">标题</th>'
            
            # 根据题目类型添加不同的列
            if model_name == 'mcqquestion':
                html += '<th style="padding: 8px; text-align: center;">选项数</th>'
                html += '<th style="padding: 8px; text-align: center;">正确答案</th>'
            elif model_name == 'lsadialog':
                html += '<th style="padding: 8px; text-align: center;">问题数</th>'
                html += '<th style="padding: 8px; text-align: center;">状态</th>'
            elif model_name == 'opitopic':
                html += '<th style="padding: 8px; text-align: center;">问题数</th>'
                html += '<th style="padding: 8px; text-align: center;">顺序</th>'
            elif model_name == 'retellitem':
                html += '<th style="padding: 8px; text-align: center;">音频</th>'
                html += '<th style="padding: 8px; text-align: center;">回答数</th>'
            
            html += '<th style="padding: 8px; text-align: center;">创建时间</th>'
            html += '<th style="padding: 8px; text-align: center;">操作</th>'
            html += '</tr></thead><tbody>'
            
            for q in questions[:20]:  # 最多显示20条
                title = str(q)[:50]
                html += f'''
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px;">{q.id}</td>
                    <td style="padding: 8px;">{title}</td>
                '''
                
                # 根据题目类型添加额外信息
                if model_name == 'mcqquestion':
                    # MCQ 选择题
                    choice_count = q.choices.count()
                    correct_choice = q.choices.filter(is_correct=True).first()
                    correct_label = correct_choice.label if correct_choice else '-'
                    html += f'<td style="padding: 8px; text-align: center;">{choice_count}</td>'
                    html += f'<td style="padding: 8px; text-align: center;"><span style="color: green; font-weight: bold;">{correct_label}</span></td>'
                elif model_name == 'lsadialog':
                    # LSA 听力简答
                    question_count = q.questions.count()
                    status = '启用' if q.is_active else '禁用'
                    status_color = '#28a745' if q.is_active else '#dc3545'
                    html += f'<td style="padding: 8px; text-align: center;">{question_count}</td>'
                    html += f'<td style="padding: 8px; text-align: center;"><span style="color: {status_color};">{status}</span></td>'
                elif model_name == 'opitopic':
                    # OPI 话题
                    question_count = q.questions.count()
                    html += f'<td style="padding: 8px; text-align: center;">{question_count}</td>'
                    html += f'<td style="padding: 8px; text-align: center;">{q.order}</td>'
                elif model_name == 'retellitem':
                    # 故事复述
                    has_audio = '✓' if q.audio_asset else '-'
                    audio_color = '#28a745' if q.audio_asset else '#999'
                    response_count = q.responses.count()
                    html += f'<td style="padding: 8px; text-align: center;"><span style="color: {audio_color};">{has_audio}</span></td>'
                    html += f'<td style="padding: 8px; text-align: center;">{response_count}</td>'
                
                # 创建时间
                created_time = q.created_at.strftime('%Y-%m-%d') if hasattr(q, 'created_at') else '-'
                html += f'''
                    <td style="padding: 8px; text-align: center; color: #666; font-size: 12px;">{created_time}</td>
                    <td style="padding: 8px; text-align: center;">
                        <a href="/admin/{app_name}/{model_name}/{q.id}/change/" target="_blank" style="color: #007bff;">
                            编辑
                        </a>
                    </td>
                </tr>
                '''
            
            if count > 20:
                col_count = 6 if model_name in ['mcqquestion', 'lsadialog', 'opitopic', 'retellitem'] else 4
                html += f'<tr><td colspan="{col_count}" style="padding: 8px; text-align: center; color: #666;">还有 {count - 20} 道题...</td></tr>'
            
            html += '</tbody></table></div>'
        
        # 添加管理按钮
        html += f'''
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <a href="/admin/{app_name}/{model_name}/?{filter_param}={obj.id}" 
                   target="_blank"
                   style="display: inline-block; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">
                    <i class="fas fa-list"></i> 查看所有关联题目
                </a>
                <a href="/admin/{app_name}/{model_name}/add/" 
                   target="_blank"
                   style="display: inline-block; padding: 8px 16px; background: #28a745; color: white; text-decoration: none; border-radius: 4px;">
                    <i class="fas fa-plus"></i> 添加新题目
                </a>
            </div>
        </div>
        '''
        
        return mark_safe(html)
    
    def _render_atc_links(self, obj):
        """渲染ATC场景链接"""
        count = obj.atc_scenarios.count()
        scenarios = obj.atc_scenarios.all()
        
        html = f'''
        <div style="padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff; border-radius: 4px;">
            <div style="margin-bottom: 10px;">
                <strong style="font-size: 14px;">📝 ATC模拟通话场景</strong>
                <span style="margin-left: 10px; color: #666;">共 {count} 个场景</span>
            </div>
        '''
        
        if count > 0:
            html += '<div style="margin: 10px 0; max-height: 300px; overflow-y: auto;">'
            html += '<table style="width: 100%; border-collapse: collapse;">'
            html += '<thead><tr style="background: #e9ecef;">'
            html += '<th style="padding: 8px; text-align: left;">ID</th>'
            html += '<th style="padding: 8px; text-align: left;">场景标题</th>'
            html += '<th style="padding: 8px; text-align: center;">机场</th>'
            html += '<th style="padding: 8px; text-align: center;">轮次数</th>'
            html += '<th style="padding: 8px; text-align: center;">状态</th>'
            html += '<th style="padding: 8px; text-align: center;">创建时间</th>'
            html += '<th style="padding: 8px; text-align: center;">操作</th>'
            html += '</tr></thead><tbody>'
            
            for scenario in scenarios[:20]:
                turn_count = scenario.turns.filter(is_active=True).count()
                airport_name = scenario.airport.name if scenario.airport else '-'
                status = '启用' if scenario.is_active else '禁用'
                status_color = '#28a745' if scenario.is_active else '#dc3545'
                created_time = scenario.created_at.strftime('%Y-%m-%d')
                
                html += f'''
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px;">{scenario.id}</td>
                    <td style="padding: 8px;">{scenario.title}</td>
                    <td style="padding: 8px; text-align: center;">{airport_name}</td>
                    <td style="padding: 8px; text-align: center;">{turn_count}</td>
                    <td style="padding: 8px; text-align: center;"><span style="color: {status_color};">{status}</span></td>
                    <td style="padding: 8px; text-align: center; color: #666; font-size: 12px;">{created_time}</td>
                    <td style="padding: 8px; text-align: center;">
                        <a href="/admin/atc/atcscenario/{scenario.id}/change/" target="_blank" style="color: #007bff;">
                            编辑
                        </a>
                    </td>
                </tr>
                '''
            
            if count > 20:
                html += f'<tr><td colspan="7" style="padding: 8px; text-align: center; color: #666;">还有 {count - 20} 个场景...</td></tr>'
            
            html += '</tbody></table></div>'
        
        html += f'''
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <a href="/admin/atc/atcscenario/?module__id__exact={obj.id}" 
                   target="_blank"
                   style="display: inline-block; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">
                    <i class="fas fa-list"></i> 查看所有关联场景
                </a>
                <a href="/admin/atc/atcscenario/add/" 
                   target="_blank"
                   style="display: inline-block; padding: 8px 16px; background: #28a745; color: white; text-decoration: none; border-radius: 4px;">
                    <i class="fas fa-plus"></i> 添加新场景
                </a>
            </div>
        </div>
        '''
        
        return mark_safe(html)
    
    questions_display.short_description = '关联的试题'
