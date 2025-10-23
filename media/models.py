from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator, FileExtensionValidator
from django.utils import timezone
import os


def media_upload_path(instance, filename):
    """
    根据媒体类型动态生成上传路径
    """
    # 根据媒体类型分类存储
    type_folder = {
        'audio': 'audio',
        'image': 'image',
        'video': 'video',
        'doc': 'document'
    }.get(instance.media_type, 'other')
    
    return f'{type_folder}/{filename}'


class MediaAsset(models.Model):
    """
    媒体资源实体类，用于映射数据库中的 'media_assets' 表。
    该实体类代表了系统中的各种媒体资产，例如音频、图像、视频和文档。
    """
    MEDIA_TYPE = [
        ('audio', '音频'),
        ('image', '图像'),
        ('video', '视频'),
        ('doc', '文档'),
    ]

    # 媒体类型，使用枚举存储，非空
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE,
        null=False,
        verbose_name='媒体类型'
    )

    # 媒体资源的统一资源标识符 (URI)，非空
    uri = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='资源URI',
        help_text='外部资源URL或相对路径'
    )
    
    # 上传的文件
    file = models.FileField(
        upload_to=media_upload_path,
        null=True,
        blank=True,
        verbose_name='上传文件',
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'mp3', 'wav', 'ogg', 'm4a', 'aac',  # 音频
                    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg',  # 图像
                    'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',  # 视频
                    'pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx'  # 文档
                ]
            )
        ]
    )
    
    # 文件大小（字节）
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='文件大小（字节）'
    )

    # 媒体持续时长，单位为毫秒
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='时长（毫秒）'
    )
    
    # 文件描述
    description = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='文件描述'
    )

    # 记录创建时间，自动设置，不可更新
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'media_assets'
        verbose_name = '媒体资源'
        verbose_name_plural = '媒体资源'
        ordering = ['-created_at']

    def __str__(self):
        if self.file:
            return f"{self.get_media_type_display()}: {os.path.basename(self.file.name)}"
        return f"{self.get_media_type_display()}: {self.uri[:50]}..."
    
    def save(self, *args, **kwargs):
        """保存时自动更新文件大小和URI"""
        if self.file:
            # 自动设置文件大小
            if not self.file_size:
                self.file_size = self.file.size
            # 如果没有URI，使用file的URL
            if not self.uri:
                self.uri = self.file.name
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """获取格式化的文件大小"""
        if not self.file_size:
            return '-'
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def get_file_url(self):
        """获取文件访问URL"""
        if self.file:
            return self.file.url
        return self.uri

