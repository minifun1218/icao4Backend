"""
ATC Admin 配置
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
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
    verbose_name = 'ATC轮次'
    verbose_name_plural = 'ATC轮次'


class KeyValueWidget(forms.Widget):
    """键值对编辑器控件"""
    template_name = 'admin/atc/key_value_widget.html'
    
    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is None:
            attrs = {}
        attrs['class'] = attrs.get('class', '') + ' key-value-widget'
        self.attrs = attrs
    
    def render(self, name, value, attrs=None, renderer=None):
        """渲染键值对编辑器"""
        import json
        
        # 解析JSON数据
        data = {}
        if value is not None:
            if isinstance(value, str):
                try:
                    data = json.loads(value)
                    if not isinstance(data, dict):
                        data = {}
                except:
                    data = {}
            elif isinstance(value, dict):
                data = value
            else:
                data = {}
        
        # 构建HTML
        html = f'''
        <div class="key-value-editor" data-name="{name}">
            <input type="hidden" name="{name}" id="id_{name}" value='{json.dumps(data, ensure_ascii=False)}'>
            <div class="key-value-pairs" id="key-value-pairs-{name}">
        '''
        
        # 添加现有的键值对
        if data:
            for key, val in data.items():
                # HTML转义，防止XSS攻击
                safe_key = str(key).replace('"', '&quot;').replace("'", '&#39;')
                safe_val = str(val).replace('"', '&quot;').replace("'", '&#39;')
                html += f'''
                <div class="key-value-pair">
                    <input type="text" class="kv-key" value="{safe_key}" placeholder="键">
                    <input type="text" class="kv-value" value="{safe_val}" placeholder="值">
                    <button type="button" class="btn-remove" onclick="removeKeyValuePair(this)">删除</button>
                </div>
                '''
        
        html += '''
            </div>
            <button type="button" class="btn-add" onclick="addKeyValuePair(this)">➕ 添加键值对</button>
        </div>
        
        <style>
            .key-value-editor {
                margin: 10px 0;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: #f9f9f9;
            }
            .key-value-pairs {
                margin-bottom: 10px;
            }
            .key-value-pair {
                display: flex;
                gap: 10px;
                margin-bottom: 8px;
                align-items: center;
            }
            .key-value-pair .kv-key {
                flex: 0 0 200px;
                padding: 6px 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            .key-value-pair .kv-value {
                flex: 1;
                padding: 6px 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            .key-value-pair .btn-remove {
                padding: 6px 12px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
            }
            .key-value-pair .btn-remove:hover {
                background: #c82333;
            }
            .btn-add {
                padding: 8px 16px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                font-size: 14px;
            }
            .btn-add:hover {
                background: #218838;
            }
        </style>
        
        <script>
            function addKeyValuePair(button) {
                const editor = button.closest('.key-value-editor');
                const container = editor.querySelector('.key-value-pairs');
                const name = editor.dataset.name;
                
                const pairDiv = document.createElement('div');
                pairDiv.className = 'key-value-pair';
                pairDiv.innerHTML = `
                    <input type="text" class="kv-key" placeholder="键">
                    <input type="text" class="kv-value" placeholder="值">
                    <button type="button" class="btn-remove" onclick="removeKeyValuePair(this)">删除</button>
                `;
                
                container.appendChild(pairDiv);
                updateHiddenInput(editor, name);
                
                // 为新输入框添加变化监听
                pairDiv.querySelectorAll('input').forEach(input => {
                    input.addEventListener('input', () => updateHiddenInput(editor, name));
                });
            }
            
            function removeKeyValuePair(button) {
                const editor = button.closest('.key-value-editor');
                const name = editor.dataset.name;
                button.closest('.key-value-pair').remove();
                updateHiddenInput(editor, name);
            }
            
            function updateHiddenInput(editor, name) {
                const pairs = editor.querySelectorAll('.key-value-pair');
                const data = {};
                
                pairs.forEach(pair => {
                    const key = pair.querySelector('.kv-key').value.trim();
                    const value = pair.querySelector('.kv-value').value.trim();
                    if (key) {
                        data[key] = value;
                    }
                });
                
                const hiddenInput = editor.querySelector('input[type="hidden"]');
                hiddenInput.value = JSON.stringify(data);
            }
            
            // 为所有键值对输入框添加变化监听
            document.addEventListener('DOMContentLoaded', function() {
                document.querySelectorAll('.key-value-editor').forEach(editor => {
                    const name = editor.dataset.name;
                    editor.querySelectorAll('input.kv-key, input.kv-value').forEach(input => {
                        input.addEventListener('input', () => updateHiddenInput(editor, name));
                    });
                });
            });
        </script>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """从表单数据中获取值"""
        import json
        value = data.get(name)
        
        if not value:
            return {}
        
        # 如果已经是字典，直接返回
        if isinstance(value, dict):
            return value
        
        # 如果是字符串，尝试解析为JSON
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                # 确保解析结果是字典
                if isinstance(parsed, dict):
                    return parsed
                else:
                    return {}
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        
        return {}


class KeyValueField(forms.Field):
    """自定义键值对字段"""
    widget = KeyValueWidget
    
    def __init__(self, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(**kwargs)
        self.widget = KeyValueWidget()
    
    def to_python(self, value):
        """将输入值转换为Python对象"""
        if value in self.empty_values:
            return {}
        
        if isinstance(value, dict):
            return value
        
        if isinstance(value, str):
            import json
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        return {}
    
    def prepare_value(self, value):
        """准备显示的值"""
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            import json
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except:
                pass
        return {}
    
    def bound_data(self, data, initial):
        """处理绑定数据 - 这个方法很重要，避免Django尝试解析JSON"""
        if data is None:
            return initial
        return data


class AtcScenarioAdminForm(forms.ModelForm):
    """ATC场景管理表单"""
    description = KeyValueField(
        label='场景描述',
        help_text='使用下方的键值对编辑器添加场景描述信息'
    )
    
    class Meta:
        model = AtcScenario
        fields = '__all__'


@admin.register(AtcScenario)
class AtcScenarioAdmin(admin.ModelAdmin):
    """
    ATC场景后台管理
    """
    form = AtcScenarioAdminForm
    
    list_display = [
        'id',
        'title',
        'airport',
        'module_display',
        'description_preview',
        'is_active',
        'turn_count',
        'created_at'
    ]
    list_filter = ['is_active', 'airport', 'module', 'created_at']
    search_fields = ['title', 'airport__name', 'airport__icao']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'airport', 'is_active', 'created_at', 'updated_at'),
            'description': '💡 提示：场景的基本信息'
        }),
        ('关联试题模块（可选）', {
            'fields': ('module',),
            'description': '💡 可选：选择该场景所属的试题模块（可多选），也可以不选择任何模块'
        }),

    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    filter_horizontal = ['module']
    
    inlines = [AtcTurnInline]
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """自定义多对多字段的查询集，只显示 ATC 类型的考试模块"""
        if db_field.name == "module":
            kwargs["queryset"] = db_field.related_model.objects.filter(
                module_type='ATC',
                is_activate=True
            ).order_by('display_order', 'created_at')
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def description_preview(self, obj):
        """显示场景描述预览"""
        if obj.description:
            import json
            try:
                # 格式化显示前3个键值对
                items = list(obj.description.items())[:3]
                preview = ', '.join([f'{k}: {v}' for k, v in items])
                if len(obj.description) > 3:
                    preview += f' ... (+{len(obj.description) - 3}项)'
                return format_html('<span style="color: #666; font-size: 12px;">{}</span>', preview)
            except:
                return format_html('<span style="color: #999;">JSON格式</span>')
        return format_html('<span style="color: #999;">-</span>')
    description_preview.short_description = '场景描述'
    
    def module_display(self, obj):
        """显示关联的模块"""
        modules = obj.module.all()
        if modules.exists():
            module_names = [m.title or m.get_module_type_display() for m in modules[:3]]
            result = ', '.join(module_names)
            if modules.count() > 3:
                result += f' 等{modules.count()}个'
            return result
        return format_html('<span style="color: #999;">未关联模块</span>')
    module_display.short_description = '关联模块'
    
    def turn_count(self, obj):
        """显示轮次数量"""
        count = obj.atc_turns.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<span style="color: #17a2b8; font-weight: bold;">{} 个轮次</span>',
                count
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
            'fields': ('scenario', 'turn_number', 'audio', 'audio_player_display','speaker_type','is_active','created_at', 'updated_at'),
            'description': '💡 选择场景、设置轮次序号和说话者类型'
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'audio_player_display']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """自定义外键字段的查询集"""
        if db_field.name == "scenario":
            # 只显示激活的ATC场景
            kwargs["queryset"] = db_field.related_model.objects.filter(
                is_active=True
            ).order_by('airport__name', 'title')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
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
        if obj.atc_turn:
            speaker = '👨‍✈️' if obj.atc_turn.speaker_type == 'pilot' else '🗼'
            if obj.atc_turn.scenario:
                return f'{speaker} {obj.atc_turn.scenario.title} - T{obj.atc_turn.turn_number}'
            return f'{speaker} T{obj.atc_turn.turn_number}'
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
