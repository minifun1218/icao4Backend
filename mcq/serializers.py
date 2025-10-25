"""
MCQ (听力选择题) 序列化器
"""
from rest_framework import serializers
from .models import McqMaterial, McqQuestion, McqChoice, McqResponse


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
    audio_url = serializers.SerializerMethodField()
    
    class Meta(McqQuestionSerializer.Meta):
        fields = McqQuestionSerializer.Meta.fields + ['choices', 'audio_url']
    
    def get_audio_url(self, obj):
        """获取音频URL（优先使用材料音频）"""
        return obj.get_audio_url()


class McqMaterialSerializer(serializers.ModelSerializer):
    """MCQ听力材料序列化器"""
    audio_url = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = McqMaterial
        fields = [
            'id',
            'title',
            'description',
            'audio_url',
            'difficulty',
            'question_count',
            'display_order'
        ]
        read_only_fields = ['id']
    
    def get_audio_url(self, obj):
        """获取音频URL"""
        if obj.audio_asset:
            return obj.audio_asset.get_file_url()
        return None
    
    def get_question_count(self, obj):
        """获取问题数量"""
        return obj.questions.count()


class McqMaterialWithQuestionsSerializer(McqMaterialSerializer):
    """MCQ听力材料详情序列化器（包含所有问题和选项）"""
    questions = serializers.SerializerMethodField()
    
    class Meta(McqMaterialSerializer.Meta):
        fields = McqMaterialSerializer.Meta.fields + ['questions']
    
    def get_questions(self, obj):
        """获取材料下的所有问题（包含选项）"""
        questions = obj.questions.all().prefetch_related('choices')
        return McqQuestionWithChoicesSerializer(questions, many=True, context=self.context).data


class McqQuestionWithChoicesSerializer(serializers.ModelSerializer):
    """题目序列化器（包含选项，不包含音频，因为使用材料音频）"""
    choices = McqChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = McqQuestion
        fields = [
            'id',
            'text_stem',
            'choices'
        ]
        read_only_fields = ['id']


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
            'mode_type',
            'answered_at',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'answered_at']


class McqResponseCreateSerializer(serializers.ModelSerializer):
    """创建MCQ答题记录序列化器"""
    
    class Meta:
        model = McqResponse
        fields = [
            'question',
            'selected_choice',
            'is_correct',
            'is_timeout',
            'mode_type'
        ]
        read_only_fields = ['is_correct']
    
    def create(self, validated_data):
        # 自动判断是否正确
        selected_choice = validated_data.get('selected_choice')
        if selected_choice:
            validated_data['is_correct'] = selected_choice.is_correct
        else:
            validated_data['is_correct'] = False
        
        return super().create(validated_data)

