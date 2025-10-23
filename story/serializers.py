"""
Story (故事复述) 序列化器
"""
from rest_framework import serializers
from .models import RetellItem, RetellResponse


class RetellItemSerializer(serializers.ModelSerializer):
    """复述题目序列化器"""
    response_count = serializers.SerializerMethodField()
    audio_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RetellItem
        fields = [
            'id',
            'title',
            'audio_asset',
            'audio_info',
            'response_count',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_response_count(self, obj):
        """获取回答数量"""
        return obj.responses.count()
    
    def get_audio_info(self, obj):
        """获取音频信息"""
        if obj.audio_asset:
            return {
                'id': obj.audio_asset.id,
                'uri': obj.audio_asset.uri,
                'duration_ms': obj.audio_asset.duration_ms
            }
        return None


class RetellResponseSerializer(serializers.ModelSerializer):
    """复述回答序列化器"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    item_title = serializers.CharField(source='retell_item.title', read_only=True)
    
    class Meta:
        model = RetellResponse
        fields = [
            'id',
            'retell_item',
            'item_title',
            'user',
            'user_name',
            'answer_audio',
            'is_timeout',
            'score',
            'answered_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'answered_at']

