"""
Vocab (航空词汇) 序列化器
"""
from rest_framework import serializers
from .models import AvVocabTopic, AvVocab, UserVocabLearning, UserTermLearning


class AvVocabTopicSerializer(serializers.ModelSerializer):
    """航空词汇主题序列化器"""
    vocab_count = serializers.SerializerMethodField()
    user_learning_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = AvVocabTopic
        fields = [
            'id',
            'code',
            'name_zh',
            'name_en',
            'description',
            'display_order',
            'vocab_count',
            'user_learning_stats',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_vocab_count(self, obj):
        """获取词汇数量"""
        return obj.vocabs.count()
    
    def get_user_learning_stats(self, obj):
        """获取用户学习统计"""
        request = self.context.get('request')
        
        # 如果没有请求对象或用户未登录，返回None
        if not request or not request.user or not request.user.is_authenticated:
            return None
        
        user = request.user
        
        # 统计该主题下用户的学习情况
        learned_count = UserVocabLearning.objects.filter(
            user=user,
            vocab__topic=obj
        ).count()
        
        favorited_count = UserVocabLearning.objects.filter(
            user=user,
            vocab__topic=obj,
            is_favorited=True
        ).count()
        
        mastered_count = UserVocabLearning.objects.filter(
            user=user,
            vocab__topic=obj,
            is_mastered=True
        ).count()
        
        total_count = obj.vocabs.count()
        
        return {
            'learned_count': learned_count,
            'favorited_count': favorited_count,
            'mastered_count': mastered_count,
            'total_count': total_count,
            'learned_percentage': round((learned_count / total_count * 100) if total_count > 0 else 0, 2),
            'mastered_percentage': round((mastered_count / total_count * 100) if total_count > 0 else 0, 2),
            'progress_percentage': round((mastered_count / total_count * 100) if total_count > 0 else 0, 2)  # 默认使用掌握进度
        }


class AvVocabSerializer(serializers.ModelSerializer):
    """航空词汇序列化器"""
    topic_name = serializers.CharField(source='topic.name_zh', read_only=True)
    cefr_level_display = serializers.CharField(source='get_cefr_level_display', read_only=True)
    audio_info = serializers.SerializerMethodField()
    user_learning_status = serializers.SerializerMethodField()
    
    class Meta:
        model = AvVocab
        fields = [
            'id',
            'headword',
            'lemma',
            'pos',
            'ipa',
            'definition_zh',
            'example_en',
            'example_zh',
            'cefr_level',
            'cefr_level_display',
            'audio_asset',
            'audio_info',
            'topic',
            'topic_name',
            'user_learning_status',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_audio_info(self, obj):
        """获取音频信息"""
        if obj.audio_asset:
            return {
                'id': obj.audio_asset.id,
                'uri': obj.audio_asset.uri,
                'duration_ms': obj.audio_asset.duration_ms
            }
        return None
    
    def get_user_learning_status(self, obj):
        """获取用户学习状态"""
        request = self.context.get('request')
        
        # 如果没有请求对象或用户未登录，返回None
        if not request or not request.user or not request.user.is_authenticated:
            return None
        
        user = request.user
        
        # 查询用户对该词汇的学习记录
        try:
            learning = UserVocabLearning.objects.get(user=user, vocab=obj)
            return {
                'is_learned': True,
                'study_count': learning.study_count,
                'mastery_level': learning.mastery_level,
                'mastery_level_display': learning.get_mastery_level_display(),
                'is_favorited': learning.is_favorited,
                'is_mastered': learning.is_mastered,
                'last_learned_at': learning.last_learned_at,
                'notes': learning.notes
            }
        except UserVocabLearning.DoesNotExist:
            return {
                'is_learned': False,
                'study_count': 0,
                'mastery_level': 0,
                'mastery_level_display': '未掌握',
                'is_favorited': False,
                'is_mastered': False,
                'last_learned_at': None,
                'notes': None
            }


class UserVocabLearningSerializer(serializers.ModelSerializer):
    """用户词汇学习记录序列化器"""
    vocab_info = serializers.SerializerMethodField()
    mastery_level_display = serializers.CharField(source='get_mastery_level_display', read_only=True)
    
    class Meta:
        model = UserVocabLearning
        fields = [
            'id', 'user', 'vocab', 'vocab_info',
            'study_count', 'mastery_level', 'mastery_level_display',
            'is_favorited', 'is_mastered',
            'first_learned_at', 'last_learned_at', 'next_review_at',
            'notes'
        ]
        read_only_fields = ['id', 'user', 'first_learned_at']
    
    def get_vocab_info(self, obj):
        """获取词汇基本信息"""
        return {
            'id': obj.vocab.id,
            'headword': obj.vocab.headword,
            'ipa': obj.vocab.ipa,
            'definition_zh': obj.vocab.definition_zh,
            'topic_name': obj.vocab.topic.name_zh if obj.vocab.topic else None
        }


class UserTermLearningSerializer(serializers.ModelSerializer):
    """用户术语学习记录序列化器"""
    term_info = serializers.SerializerMethodField()
    mastery_level_display = serializers.CharField(source='get_mastery_level_display', read_only=True)
    
    class Meta:
        model = UserTermLearning
        fields = [
            'id', 'user', 'term', 'term_info',
            'study_count', 'mastery_level', 'mastery_level_display',
            'is_favorited', 'is_mastered',
            'first_learned_at', 'last_learned_at', 'next_review_at',
            'notes'
        ]
        read_only_fields = ['id', 'user', 'first_learned_at']
    
    def get_term_info(self, obj):
        """获取术语基本信息"""
        return {
            'id': obj.term.id,
            'headword': obj.term.headword,
            'ipa': obj.term.ipa,
            'definition_zh': obj.term.definition_zh,
            'topic_name': obj.term.topic.name_zh if obj.term.topic else None
        }

