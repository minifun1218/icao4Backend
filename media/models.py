from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator, FileExtensionValidator
from django.utils import timezone
import os
import logging

logger = logging.getLogger(__name__)


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
    
    # 音频比特率（仅音频）
    bitrate = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='比特率（bps）',
        help_text='音频/视频的比特率'
    )
    
    # 音频采样率（仅音频）
    sample_rate = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='采样率（Hz）',
        help_text='音频的采样率'
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
    
    def _get_audio_info(self, file_path):
        """获取音频信息（时长、比特率、采样率）"""
        try:
            from mutagen import File
            audio = File(file_path)
            
            if audio is None:
                logger.error(f"Mutagen无法识别文件类型: {file_path}")
                return None
            
            if audio.info is None:
                logger.error(f"Mutagen无法解析音频流信息，文件可能已损坏: {file_path}")
                return None
            
            # 提取音频信息
            info = {
                'duration_ms': None,
                'bitrate': None,
                'sample_rate': None,
            }
            
            # 时长（转换为毫秒）
            if hasattr(audio.info, 'length'):
                info['duration_ms'] = int(audio.info.length * 1000)
                logger.info(f"音频时长: {audio.info.length:.2f}秒")
            
            # 比特率
            if hasattr(audio.info, 'bitrate'):
                info['bitrate'] = audio.info.bitrate
                logger.info(f"音频比特率: {audio.info.bitrate / 1000:.1f} kbps")
            
            # 采样率
            if hasattr(audio.info, 'sample_rate'):
                info['sample_rate'] = audio.info.sample_rate
                logger.info(f"音频采样率: {audio.info.sample_rate} Hz")
            
            return info
            
        except ImportError:
            logger.warning("mutagen库未安装，无法自动识别音频信息。请运行: pip install mutagen")
        except Exception as e:
            logger.error(f"读取音频信息失败: {str(e)}", exc_info=True)
        return None
    
    def _get_video_duration(self, file_path):
        """获取视频时长（毫秒）"""
        try:
            from moviepy.editor import VideoFileClip
            with VideoFileClip(file_path) as video:
                return int(video.duration * 1000)  # 转换为毫秒
        except ImportError:
            logger.warning("moviepy库未安装，无法自动识别视频时长。请运行: pip install moviepy")
        except Exception as e:
            logger.error(f"读取视频时长失败: {str(e)}")
        return None
    
    def save(self, *args, **kwargs):
        """保存时自动更新文件大小、URI、时长和音频信息"""
        if self.file:
            # 自动设置文件大小
            if not self.file_size:
                self.file_size = self.file.size
            
            # 自动识别音频/视频信息
            if not self.duration_ms and self.media_type in ['audio', 'video']:
                # 先保存文件以便读取
                is_new = self.pk is None
                if is_new:
                    super().save(*args, **kwargs)
                
                # 获取文件路径
                file_path = self.file.path
                
                # 根据类型识别信息
                if self.media_type == 'audio':
                    audio_info = self._get_audio_info(file_path)
                    if audio_info:
                        # 更新所有音频信息
                        if audio_info.get('duration_ms'):
                            self.duration_ms = audio_info['duration_ms']
                        if audio_info.get('bitrate'):
                            self.bitrate = audio_info['bitrate']
                        if audio_info.get('sample_rate'):
                            self.sample_rate = audio_info['sample_rate']
                        
                        logger.info(f"音频信息识别成功: 时长={self.duration_ms}ms, 比特率={self.bitrate}, 采样率={self.sample_rate}Hz")
                
                elif self.media_type == 'video':
                    duration = self._get_video_duration(file_path)
                    if duration:
                        self.duration_ms = duration
                        logger.info(f"自动识别视频时长: {duration}ms")
                
                # 如果是新记录且识别到信息，需要再次更新
                if is_new and (self.duration_ms or self.bitrate or self.sample_rate):
                    update_fields = {}
                    if self.duration_ms:
                        update_fields['duration_ms'] = self.duration_ms
                    if self.bitrate:
                        update_fields['bitrate'] = self.bitrate
                    if self.sample_rate:
                        update_fields['sample_rate'] = self.sample_rate
                    
                    if update_fields:
                        MediaAsset.objects.filter(pk=self.pk).update(**update_fields)
        
        # 保存（如果还未保存）
        if self.pk is None:
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
        
        # 保存后更新URI（如果上传了文件）
        if self.file and not self.uri:
            self.uri = self.file.url
            # 使用update避免再次触发save
            MediaAsset.objects.filter(pk=self.pk).update(uri=self.uri)
    
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

