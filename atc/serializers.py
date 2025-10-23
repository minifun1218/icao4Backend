"""
ATC 序列化器
"""
from rest_framework import serializers
from .models import Airport, AtcScenario, AtcTurn, AtcTurnResponse


class AirportSerializer(serializers.ModelSerializer):
    """
    机场序列化器
    """
    # 统计关联的场景数量
    scenario_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Airport
        fields = [
            'id',
            'icao',
            'name',
            'city',
            'country',
            'timezone',
            'is_active',
            'scenario_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_scenario_count(self, obj):
        """获取该机场的场景数量"""
        return obj.scenarios.filter(is_active=True).count()


class AirportListSerializer(serializers.ModelSerializer):
    """
    机场列表序列化器（简化版）
    """
    scenario_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Airport
        fields = [
            'id',
            'icao',
            'name',
            'city',
            'country',
            'is_active',
            'scenario_count'
        ]
    
    def get_scenario_count(self, obj):
        """获取该机场的场景数量"""
        return obj.scenarios.filter(is_active=True).count()


class AtcTurnSerializer(serializers.ModelSerializer):
    """
    ATC轮次序列化器
    """
    speaker_type_display = serializers.CharField(
        source='get_speaker_type_display',
        read_only=True
    )
    # 音频资源信息
    audio_info = serializers.SerializerMethodField()
    
    class Meta:
        model = AtcTurn
        fields = [
            'id',
            'turn_number',
            'speaker_type',
            'speaker_type_display',
            'audio',
            'audio_info',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_audio_info(self, obj):
        """获取音频资源信息"""
        if obj.audio:
            return {
                'id': obj.audio.id,
                'url': obj.audio.file_path if hasattr(obj.audio, 'file_path') else None,
            }
        return None


class AtcScenarioSerializer(serializers.ModelSerializer):
    """
    ATC场景序列化器
    """
    # 机场信息
    airport_name = serializers.CharField(source='airport.name', read_only=True)
    airport_icao = serializers.CharField(source='airport.icao', read_only=True)
    
    # 模块信息
    module_name = serializers.CharField(source='module.name', read_only=True)
    
    # 统计轮次数量
    turn_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AtcScenario
        fields = [
            'id',
            'airport',
            'airport_name',
            'airport_icao',
            'module',
            'module_name',
            'title',
            'description',
            'is_active',
            'turn_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_turn_count(self, obj):
        """获取该场景的轮次数量"""
        return obj.turns.filter(is_active=True).count()


class AtcScenarioListSerializer(serializers.ModelSerializer):
    """
    ATC场景列表序列化器（简化版）
    """
    airport_name = serializers.CharField(source='airport.name', read_only=True)
    airport_icao = serializers.CharField(source='airport.icao', read_only=True)
    turn_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AtcScenario
        fields = [
            'id',
            'airport_icao',
            'airport_name',
            'title',
            'is_active',
            'turn_count',
            'created_at'
        ]
    
    def get_turn_count(self, obj):
        """获取该场景的轮次数量"""
        return obj.turns.filter(is_active=True).count()


class AtcScenarioDetailSerializer(AtcScenarioSerializer):
    """
    ATC场景详情序列化器（包含所有轮次）
    """
    # 嵌套轮次列表
    turns = serializers.SerializerMethodField()
    # 完整的机场信息
    airport_detail = AirportSerializer(source='airport', read_only=True)
    
    class Meta(AtcScenarioSerializer.Meta):
        fields = AtcScenarioSerializer.Meta.fields + ['turns', 'airport_detail']
    
    def get_turns(self, obj):
        """获取该场景的所有轮次（按轮次序号排序）"""
        turns = obj.turns.filter(is_active=True).order_by('turn_number')
        return AtcTurnSerializer(turns, many=True).data


class AtcTurnDetailSerializer(AtcTurnSerializer):
    """
    ATC轮次详情序列化器（包含场景信息）
    """
    scenario_info = serializers.SerializerMethodField()
    
    class Meta(AtcTurnSerializer.Meta):
        fields = AtcTurnSerializer.Meta.fields + ['scenario', 'scenario_info']
    
    def get_scenario_info(self, obj):
        """获取场景基本信息"""
        if obj.scenario:
            return {
                'id': obj.scenario.id,
                'title': obj.scenario.title,
                'airport_name': obj.scenario.airport.name,
                'airport_icao': obj.scenario.airport.icao,
            }
        return None


class AtcTurnResponseSerializer(serializers.ModelSerializer):
    """
    ATC轮次回答序列化器
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    turn_info = serializers.SerializerMethodField()
    
    class Meta:
        model = AtcTurnResponse
        fields = [
            'id',
            'atc_turn',
            'turn_info',
            'user',
            'user_name',
            'audio_file_path',
            'is_timeout',
            'score',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_turn_info(self, obj):
        """获取轮次信息"""
        if obj.atc_turn:
            return {
                'id': obj.atc_turn.id,
                'turn_number': obj.atc_turn.turn_number,
                'speaker_type': obj.atc_turn.get_speaker_type_display(),
            }
        return None

