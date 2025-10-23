"""
Media (媒体资源) 序列化器
"""
from rest_framework import serializers
from .models import MediaAsset


class MediaAssetSerializer(serializers.ModelSerializer):
    """媒体资源序列化器"""
    media_type_display = serializers.CharField(source='get_media_type_display', read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaAsset
        fields = [
            'id',
            'media_type',
            'media_type_display',
            'uri',
            'duration_ms',
            'duration_seconds',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_duration_seconds(self, obj):
        """获取时长（秒）"""
        if obj.duration_ms:
            return round(obj.duration_ms / 1000, 2)
        return None

