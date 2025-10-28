"""
LSA (听力简答) 序列化器
"""
from rest_framework import serializers
from .models import LsaDialog, LsaQuestion, LsaResponse


class LsaQuestionSerializer(serializers.ModelSerializer):
    """
    LSA问题序列化器
    """
    question_audio_info = serializers.SerializerMethodField()
    
    class Meta:
        model = LsaQuestion
        fields = [
            'id',
            'question_text',
            'question_audio',
            'question_audio_info',
            'display_order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_question_audio_info(self, obj):
        """获取问题音频信息"""
        if obj.question_audio:
            return {
                'id': obj.question_audio.id,
                'uri': obj.question_audio.uri,
                'duration_ms': obj.question_audio.duration_ms
            }
        return None


class LsaDialogSerializer(serializers.ModelSerializer):
    """
    LSA对话序列化器
    """
    question_count = serializers.SerializerMethodField()
    audio_info = serializers.SerializerMethodField()
    
    class Meta:
        model = LsaDialog
        fields = [
            'id',
            'title',
            'description',
            'audio_asset',
            'audio_info',
            'display_order',
            'is_active',
            'question_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_question_count(self, obj):
        """获取问题数量"""
        return obj.lsa_questions.filter(is_active=True).count()
    
    def get_audio_info(self, obj):
        """获取音频信息"""
        if obj.audio_asset:
            return {
                'id': obj.audio_asset.id,
                'uri': obj.audio_asset.uri,
                'duration_ms': obj.audio_asset.duration_ms
            }
        return None


class LsaDialogDetailSerializer(LsaDialogSerializer):
    """
    LSA对话详情序列化器（包含所有问题）
    """
    questions = serializers.SerializerMethodField()
    
    class Meta(LsaDialogSerializer.Meta):
        fields = LsaDialogSerializer.Meta.fields + ['questions']
    
    def get_questions(self, obj):
        """获取所有问题"""
        questions = obj.lsa_questions.filter(is_active=True).order_by('display_order')
        return LsaQuestionSerializer(questions, many=True).data


class LsaResponseSerializer(serializers.ModelSerializer):
    """
    LSA回答序列化器
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    
    class Meta:
        model = LsaResponse
        fields = [
            'id',
            'question',
            'question_text',
            'user',
            'user_name',
            'answer_audio',
            'is_timeout',
            'answered_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'answered_at']

