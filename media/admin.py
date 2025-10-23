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
    媒体资源后台管理（支持预览）
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
    
    fieldsets = (
        ('基本信息', {
            'fields': ('media_type', 'description')
        }),
        ('文件上传', {
            'fields': ('file', 'uri'),
            'description': '可以上传文件或填写外部资源URL'
        }),
        ('文件属性', {
            'fields': ('file_size', 'duration_ms'),
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
    
    readonly_fields = ['created_at', 'file_size', 'preview_display']
    
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
        """显示时长（格式化）"""
        if obj.duration_ms:
            seconds = obj.duration_ms / 1000
            if seconds < 60:
                return f"{seconds:.1f}秒"
            else:
                minutes = seconds / 60
                return f"{minutes:.1f}分钟"
        return '-'
    duration_display.short_description = '时长'
    
    def file_preview(self, obj):
        """列表页小预览图标"""
        if obj.media_type == 'image' and obj.file:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.file.url
            )
        elif obj.media_type == 'audio':
            return format_html('<i class="fas fa-file-audio" style="font-size: 30px; color: #17a2b8;"></i>')
        elif obj.media_type == 'video':
            return format_html('<i class="fas fa-file-video" style="font-size: 30px; color: #dc3545;"></i>')
        elif obj.media_type == 'doc':
            return format_html('<i class="fas fa-file-alt" style="font-size: 30px; color: #ffc107;"></i>')
        return '-'
    file_preview.short_description = '预览'
    
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
    
    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',)
        }
