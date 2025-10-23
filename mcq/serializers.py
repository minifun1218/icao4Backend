"""
MCQ (听力选择题) 序列化器
"""
from rest_framework import serializers
from .models import McqQuestion, McqChoice, McqResponse


class McqChoiceSerializer(serializers.ModelSerializer):
    """选择题选项序列化器"""
    
    class Meta:
        model = McqChoice
        fields = [
            'id',
            'label',
            'content',
            'is_correct'
        ]
        read_only_fields = ['id']


class McqQuestionSerializer(serializers.ModelSerializer):
    """听力选择题序列化器"""
    choice_count = serializers.SerializerMethodField()
    audio_info = serializers.SerializerMethodField()
    
    class Meta:
        model = McqQuestion
        fields = [
            'id',
            'text_stem',
            'audio_asset',
            'audio_info',
            'choice_count',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_choice_count(self, obj):
        """获取选项数量"""
        return obj.choices.count()
    
    def get_audio_info(self, obj):
        """获取音频信息"""
        if obj.audio_asset:
            return {
                'id': obj.audio_asset.id,
                'uri': obj.audio_asset.uri,
                'duration_ms': obj.audio_asset.duration_ms
            }
        return None


class McqQuestionDetailSerializer(McqQuestionSerializer):
    """听力选择题详情序列化器（包含所有选项）"""
    choices = McqChoiceSerializer(many=True, read_only=True)
    
    class Meta(McqQuestionSerializer.Meta):
        fields = McqQuestionSerializer.Meta.fields + ['choices']


class McqResponseSerializer(serializers.ModelSerializer):
    """选择题作答记录序列化器"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    question_text = serializers.CharField(source='question.text_stem', read_only=True)
    selected_choice_label = serializers.CharField(source='selected_choice.label', read_only=True)
    
    class Meta:
        model = McqResponse
        fields = [
            'id',
            'question',
            'question_text',
            'user',
            'user_name',
            'selected_choice',
            'selected_choice_label',
            'is_correct',
            'is_timeout',
            'answered_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'answered_at']

