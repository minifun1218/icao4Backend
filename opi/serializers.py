"""
OPI (口语面试) 序列化器
"""
from rest_framework import serializers
from .models import OpiTopic, OpiQuestion, OpiResponse


class OpiQuestionSerializer(serializers.ModelSerializer):
    """OPI问题序列化器"""
    prompt_audio_info = serializers.SerializerMethodField()
    
    class Meta:
        model = OpiQuestion
        fields = [
            'id',
            'QOrder',
            'prompt_audio',
            'prompt_audio_info',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_prompt_audio_info(self, obj):
        """获取提问音频信息"""
        if obj.prompt_audio:
            return {
                'id': obj.prompt_audio.id,
                'uri': obj.prompt_audio.uri,
                'duration_ms': obj.prompt_audio.duration_ms
            }
        return None


class OpiTopicSerializer(serializers.ModelSerializer):
    """OPI话题序列化器"""
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = OpiTopic
        fields = [
            'id',
            'order',
            'title',
            'description',
            'question_count',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_question_count(self, obj):
        """获取问题数量"""
        return obj.questions.count()


class OpiTopicDetailSerializer(OpiTopicSerializer):
    """OPI话题详情序列化器（包含所有问题）"""
    questions = serializers.SerializerMethodField()
    
    class Meta(OpiTopicSerializer.Meta):
        fields = OpiTopicSerializer.Meta.fields + ['questions']
    
    def get_questions(self, obj):
        """获取所有问题"""
        questions = obj.questions.all().order_by('QOrder')
        return OpiQuestionSerializer(questions, many=True).data


class OpiResponseSerializer(serializers.ModelSerializer):
    """OPI回答序列化器"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    topic_title = serializers.CharField(source='question.topic.title', read_only=True)
    
    class Meta:
        model = OpiResponse
        fields = [
            'id',
            'question',
            'topic_title',
            'user',
            'user_name',
            'answer_audio',
            'is_timeout',
            'score',
            'answered_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'answered_at']

