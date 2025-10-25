"""
Media (媒体资源) Admin 配置
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import MediaAsset


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    """
    媒体资源后台管理（支持预览、删除）
    """
    list_display = [
        'id',
        'media_type',
        'file_preview',
        'file_name',
        'file_size_display',
        'duration_display',
        'created_at'
    ]
    list_filter = ['media_type', 'created_at']
    search_fields = ['uri', 'description']
    ordering = ['-created_at']
    list_display_links = ['id', 'file_name']  # 可点击进入详情的字段
    
    # 启用批量删除操作
    actions = ['delete_selected', 'delete_media_with_files']
    
    # 明确启用删除权限
    def has_delete_permission(self, request, obj=None):
        """允许删除媒体资源"""
        return True
    
    def delete_model(self, request, obj):
        """删除单个对象时，同时删除物理文件"""
        import os
        if obj.file:
            # 删除物理文件
            if os.path.isfile(obj.file.path):
                os.remove(obj.file.path)
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """批量删除时，同时删除物理文件"""
        import os
        for obj in queryset:
            if obj.file:
                # 删除物理文件
                if os.path.isfile(obj.file.path):
                    os.remove(obj.file.path)
        super().delete_queryset(request, queryset)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('media_type', 'description')
        }),
        ('文件上传', {
            'fields': ('file', 'uri_display'),
            'description': '上传文件后，URI会自动生成。也可以直接填写外部资源URL（不上传文件时）'
        }),
        ('外部资源URL', {
            'fields': ('uri',),
            'description': '如果不上传文件，可以填写外部资源的URL',
            'classes': ('collapse',)
        }),
        ('文件属性', {
            'fields': ('file_size', 'duration_display_field', 'audio_info_display'),
            'description': '文件大小和音频信息会自动识别',
            'classes': ('collapse',)
        }),
        ('预览', {
            'fields': ('preview_display',),
            'classes': ('wide',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'file_size', 'preview_display', 'uri_display', 'duration_display_field', 'audio_info_display']
    
    def uri_display(self, obj):
        """显示URI（可复制）"""
        if obj.uri:
            return format_html(
                '''<div style="display: flex; align-items: center; gap: 10px;">
                    <input type="text" value="{}" readonly 
                           style="flex: 1; padding: 5px; border: 1px solid #ddd; border-radius: 4px; background: #f9f9f9;" 
                           onclick="this.select();" />
                    <button type="button" onclick="navigator.clipboard.writeText('{}'); alert('已复制到剪贴板');" 
                            class="btn btn-sm btn-info" style="padding: 5px 10px;">
                        <i class="fas fa-copy"></i> 复制
                    </button>
                    <a href="{}" target="_blank" class="btn btn-sm btn-primary" style="padding: 5px 10px;">
                        <i class="fas fa-external-link-alt"></i> 打开
                    </a>
                </div>''',
                obj.uri, obj.uri, obj.uri
            )
        return mark_safe('<span style="color: #999;">文件上传后自动生成</span>')
    uri_display.short_description = '资源URI（自动生成）'
    
    def file_name(self, obj):
        """显示文件名"""
        if obj.file:
            import os
            return os.path.basename(obj.file.name)
        elif obj.uri:
            return obj.uri[:50] + '...' if len(obj.uri) > 50 else obj.uri
        return '-'
    file_name.short_description = '文件名'
    
    def file_size_display(self, obj):
        """显示文件大小"""
        return obj.get_file_size_display()
    file_size_display.short_description = '文件大小'
    
    def duration_display(self, obj):
        """显示时长（格式化）- 用于列表"""
        if obj.duration_ms:
            seconds = obj.duration_ms / 1000
            if seconds < 60:
                return f"{seconds:.1f}秒"
            else:
                minutes = seconds / 60
                return f"{minutes:.1f}分钟"
        return '-'
    duration_display.short_description = '时长'
    
    def duration_display_field(self, obj):
        """显示时长（格式化）- 用于详情页"""
        if obj.duration_ms:
            seconds = obj.duration_ms / 1000
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            
            if minutes > 0:
                time_str = f"{minutes}分{secs}秒"
            else:
                time_str = f"{secs}秒"
            
            return format_html(
                '''<div style="padding: 10px; background: #f0f8ff; border-left: 4px solid #17a2b8; border-radius: 4px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <i class="fas fa-clock" style="font-size: 24px; color: #17a2b8;"></i>
                        <div>
                            <strong style="font-size: 18px; color: #333;">{}</strong>
                            <br>
                            <span style="color: #666; font-size: 12px;">
                                ✨ 自动识别 | {} 毫秒
                            </span>
                        </div>
                    </div>
                </div>''',
                time_str, obj.duration_ms
            )
        return mark_safe(
            '''<div style="padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                <i class="fas fa-info-circle" style="color: #856404;"></i>
                <span style="color: #856404; margin-left: 5px;">
                    上传音频或视频文件后会自动识别时长
                </span>
            </div>'''
        )
    duration_display_field.short_description = '时长（自动识别）'
    
    def audio_info_display(self, obj):
        """显示音频信息（比特率、采样率）"""
        if obj.media_type != 'audio':
            return mark_safe('<span style="color: #999;">仅音频文件</span>')
        
        if obj.bitrate or obj.sample_rate:
            bitrate_display = f"{obj.bitrate / 1000:.1f} kbps" if obj.bitrate else '-'
            sample_rate_display = f"{obj.sample_rate} Hz" if obj.sample_rate else '-'
            
            return format_html(
                '''<div style="padding: 10px; background: #f0f8ff; border-left: 4px solid #17a2b8; border-radius: 4px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 5px; font-weight: bold; width: 80px;">
                                <i class="fas fa-signal" style="color: #17a2b8;"></i> 比特率:
                            </td>
                            <td style="padding: 5px;">{}</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px; font-weight: bold;">
                                <i class="fas fa-wave-square" style="color: #17a2b8;"></i> 采样率:
                            </td>
                            <td style="padding: 5px;">{}</td>
                        </tr>
                    </table>
                    <p style="color: #666; font-size: 12px; margin: 5px 0 0 0;">
                        ✨ 自动识别
                    </p>
                </div>''',
                bitrate_display, sample_rate_display
            )
        
        return mark_safe(
            '''<div style="padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                <i class="fas fa-info-circle" style="color: #856404;"></i>
                <span style="color: #856404; margin-left: 5px;">
                    上传音频文件后会自动识别比特率和采样率
                </span>
            </div>'''
        )
    audio_info_display.short_description = '音频信息（自动识别）'
    
    def file_preview(self, obj):
        """列表页预览（图片直接显示，音频/视频可点击播放）"""
        file_url = obj.get_file_url()
        if not file_url:
            return '-'
        
        if obj.media_type == 'image':
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px; cursor: pointer;" '
                'onclick="window.open(\'{}\', \'_blank\')" title="点击查看大图" />',
                file_url, file_url
            )
        elif obj.media_type == 'audio':
            # 在列表页添加可播放的音频控件
            return format_html(
                '''<div style="display: flex; align-items: center; gap: 5px;">
                    <i class="fas fa-file-audio" style="font-size: 24px; color: #17a2b8;"></i>
                    <audio controls style="height: 30px; width: 200px;" preload="none">
                        <source src="{}" type="audio/mpeg">
                    </audio>
                </div>''',
                file_url
            )
        elif obj.media_type == 'video':
            return format_html(
                '''<div style="display: flex; align-items: center; gap: 5px;">
                    <i class="fas fa-file-video" style="font-size: 24px; color: #dc3545;"></i>
                    <button onclick="playVideo_{id}()" class="btn btn-sm btn-primary" 
                            style="padding: 2px 8px; font-size: 12px;">
                        <i class="fas fa-play"></i> 播放
                    </button>
                </div>
                <script>
                function playVideo_{id}() {{
                    var modal = document.createElement('div');
                    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:9999;display:flex;align-items:center;justify-content:center;';
                    modal.innerHTML = '<div style="position:relative;max-width:90%;max-height:90%;"><video controls autoplay style="max-width:100%;max-height:90vh;"><source src="{url}" type="video/mp4"></video><button onclick="this.parentElement.parentElement.remove()" style="position:absolute;top:-30px;right:0;background:white;border:none;padding:5px 10px;cursor:pointer;border-radius:4px;">关闭</button></div>';
                    document.body.appendChild(modal);
                    modal.onclick = function(e) {{ if(e.target === modal) modal.remove(); }};
                }}
                </script>''',
                id=obj.id, url=file_url
            )
        elif obj.media_type == 'doc':
            return format_html(
                '''<div style="display: flex; align-items: center; gap: 5px;">
                    <i class="fas fa-file-alt" style="font-size: 24px; color: #ffc107;"></i>
                    <a href="{}" target="_blank" class="btn btn-sm btn-secondary" 
                       style="padding: 2px 8px; font-size: 12px;">
                        <i class="fas fa-download"></i> 下载
                    </a>
                </div>''',
                file_url
            )
        return '-'
    file_preview.short_description = '预览/播放'
    
    def preview_display(self, obj):
        """详情页完整预览"""
        if not obj.file and not obj.uri:
            return mark_safe('<p style="color: #666;">暂无文件</p>')
        
        file_url = obj.get_file_url()
        
        if obj.media_type == 'image':
            return mark_safe(f'''
                <div style="max-width: 800px;">
                    <img src="{file_url}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" />
                    <p style="margin-top: 10px; color: #666;">
                        <a href="{file_url}" target="_blank">在新窗口打开</a>
                    </p>
                </div>
            ''')
        
        elif obj.media_type == 'audio':
            return mark_safe(f'''
                <div style="max-width: 600px;">
                    <audio controls style="width: 100%;">
                        <source src="{file_url}" type="audio/mpeg">
                        您的浏览器不支持音频播放。
                    </audio>
                    <p style="margin-top: 10px; color: #666;">
                        <a href="{file_url}" target="_blank" download>下载音频</a>
                    </p>
                </div>
            ''')
        
        elif obj.media_type == 'video':
            return mark_safe(f'''
                <div style="max-width: 800px;">
                    <video controls style="width: 100%; max-height: 500px; border: 1px solid #ddd; border-radius: 4px;">
                        <source src="{file_url}" type="video/mp4">
                        您的浏览器不支持视频播放。
                    </video>
                    <p style="margin-top: 10px; color: #666;">
                        <a href="{file_url}" target="_blank" download>下载视频</a>
                    </p>
                </div>
            ''')
        
        elif obj.media_type == 'doc':
            return mark_safe(f'''
                <div style="padding: 20px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9;">
                    <i class="fas fa-file-alt" style="font-size: 48px; color: #ffc107;"></i>
                    <p style="margin-top: 10px;">
                        <strong>文档文件</strong><br>
                        <a href="{file_url}" target="_blank" download class="btn btn-primary" style="margin-top: 10px;">
                            <i class="fas fa-download"></i> 下载文档
                        </a>
                        <a href="{file_url}" target="_blank" class="btn btn-secondary" style="margin-top: 10px; margin-left: 10px;">
                            <i class="fas fa-external-link-alt"></i> 在新窗口打开
                        </a>
                    </p>
                </div>
            ''')
        
        return mark_safe(f'<a href="{file_url}" target="_blank">{file_url}</a>')
    
    preview_display.short_description = '媒体预览'
    
    def delete_media_with_files(self, request, queryset):
        """
        自定义批量删除操作（删除数据库记录和物理文件）
        """
        import os
        deleted_count = 0
        file_count = 0
        
        for obj in queryset:
            # 删除物理文件
            if obj.file:
                try:
                    if os.path.isfile(obj.file.path):
                        os.remove(obj.file.path)
                        file_count += 1
                except Exception as e:
                    self.message_user(request, f'删除文件失败: {str(e)}', level='warning')
            
            # 删除数据库记录
            obj.delete()
            deleted_count += 1
        
        self.message_user(
            request, 
            f'成功删除 {deleted_count} 条媒体记录和 {file_count} 个物理文件',
            level='success'
        )
    
    delete_media_with_files.short_description = '🗑️ 删除选中的媒体资源（含文件）'
    
    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',)
        }
