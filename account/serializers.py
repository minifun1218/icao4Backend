"""
账号相关序列化器
"""
from rest_framework import serializers
from .models import WxUser, Role, UserLearningProgress


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'status', 'created_at']


class WxUserSerializer(serializers.ModelSerializer):
    """微信用户序列化器"""
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = WxUser
        fields = [
            'id', 'openid', 'username', 'phone', 'avatar', 'avatar_url',
            'gender', 'birthday', 'level', 'location', 
            'join_date', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'openid', 'created_at', 'updated_at', 'avatar_url']
    
    def get_avatar_url(self, obj):
        """获取头像完整URL"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

class WxLoginSerializer(serializers.Serializer):
    """微信登录序列化器"""
    code = serializers.CharField(required=True, help_text="微信登录code")
    username = serializers.CharField(required=False, allow_blank=True, help_text="用户昵称")
    avatar = serializers.CharField(required=False, allow_blank=True, help_text="用户头像")
    gender = serializers.IntegerField(required=False, help_text="用户性别")


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户信息更新序列化器"""
    
    class Meta:
        model = WxUser
        fields = ['username', 'phone', 'avatar', 'gender', 'birthday', 'location']


class UserLearningProgressSerializer(serializers.ModelSerializer):
    """用户学习进度序列化器"""
    overall_progress = serializers.SerializerMethodField()
    mcq_accuracy = serializers.SerializerMethodField()
    mcq_progress = serializers.SerializerMethodField()
    lsa_progress = serializers.SerializerMethodField()
    story_progress = serializers.SerializerMethodField()
    opi_progress = serializers.SerializerMethodField()
    atc_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = UserLearningProgress
        fields = [
            'id', 'user',
            # MCQ
            'mcq_total', 'mcq_completed', 'mcq_correct',
            'mcq_practice_count', 'mcq_exam_count', 'mcq_accuracy', 'mcq_progress',
            # LSA
            'lsa_total', 'lsa_completed',
            'lsa_practice_count', 'lsa_exam_count', 'lsa_progress',
            # Story
            'story_total', 'story_completed', 'story_avg_score',
            'story_practice_count', 'story_exam_count', 'story_progress',
            # OPI
            'opi_total', 'opi_completed', 'opi_avg_score',
            'opi_practice_count', 'opi_exam_count', 'opi_progress',
            # ATC
            'atc_total', 'atc_completed', 'atc_avg_score',
            'atc_practice_count', 'atc_exam_count', 'atc_progress',
            # 总体
            'total_study_time', 'total_practice_count', 'total_exam_count',
            'continuous_days', 'last_study_date', 'overall_progress',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_overall_progress(self, obj):
        return obj.get_overall_progress()
    
    def get_mcq_accuracy(self, obj):
        return obj.get_mcq_accuracy()
    
    def get_mcq_progress(self, obj):
        return round((obj.mcq_completed / obj.mcq_total * 100) if obj.mcq_total > 0 else 0, 2)
    
    def get_lsa_progress(self, obj):
        return round((obj.lsa_completed / obj.lsa_total * 100) if obj.lsa_total > 0 else 0, 2)
    
    def get_story_progress(self, obj):
        return round((obj.story_completed / obj.story_total * 100) if obj.story_total > 0 else 0, 2)
    
    def get_opi_progress(self, obj):
        return round((obj.opi_completed / obj.opi_total * 100) if obj.opi_total > 0 else 0, 2)
    
    def get_atc_progress(self, obj):
        return round((obj.atc_completed / obj.atc_total * 100) if obj.atc_total > 0 else 0, 2)

