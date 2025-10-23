"""
Exam 序列化器
"""
from rest_framework import serializers
from .models import ExamPaper, ExamModule


class ExamModuleSerializer(serializers.ModelSerializer):
    """
    考试模块序列化器
    """
    module_type_display = serializers.CharField(
        source='get_module_type_display',
        read_only=True
    )
    
    class Meta:
        model = ExamModule
        fields = [
            'id',
            'module_type',
            'module_type_display',
            'display_order',
            'score',
            'duration',
            'is_activate',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ExamPaperSerializer(serializers.ModelSerializer):
    """
    考试试卷序列化器
    """
    # 统计关联的模块数量
    module_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamPaper
        fields = [
            'id',
            'code',
            'name',
            'total_duration_min',
            'description',
            'module_count',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_module_count(self, obj):
        """获取该试卷的模块数量"""
        return obj.exammodule_set.filter(is_activate=True).count()


class ExamPaperListSerializer(serializers.ModelSerializer):
    """
    考试试卷列表序列化器（简化版）
    """
    module_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamPaper
        fields = [
            'id',
            'code',
            'name',
            'total_duration_min',
            'module_count',
            'created_at'
        ]
    
    def get_module_count(self, obj):
        """获取该试卷的模块数量"""
        return obj.exammodule_set.filter(is_activate=True).count()


class ExamPaperDetailSerializer(ExamPaperSerializer):
    """
    考试试卷详情序列化器（包含所有模块）
    """
    # 嵌套模块列表
    modules = serializers.SerializerMethodField()
    # 总分
    total_score = serializers.SerializerMethodField()
    
    class Meta(ExamPaperSerializer.Meta):
        fields = ExamPaperSerializer.Meta.fields + ['modules', 'total_score']
    
    def get_modules(self, obj):
        """获取该试卷的所有模块（按显示顺序排序）"""
        modules = obj.exammodule_set.filter(is_activate=True).order_by('display_order')
        return ExamModuleSerializer(modules, many=True).data
    
    def get_total_score(self, obj):
        """计算试卷总分"""
        modules = obj.exammodule_set.filter(is_activate=True)
        total = sum([m.score for m in modules if m.score])
        return total


class ExamModuleDetailSerializer(ExamModuleSerializer):
    """
    考试模块详情序列化器（包含关联的试卷信息）
    """
    papers = serializers.SerializerMethodField()
    
    class Meta(ExamModuleSerializer.Meta):
        fields = ExamModuleSerializer.Meta.fields + ['papers']
    
    def get_papers(self, obj):
        """获取关联的试卷列表"""
        papers = obj.exam_paper.all()
        return [{
            'id': paper.id,
            'code': paper.code,
            'name': paper.name
        } for paper in papers]

