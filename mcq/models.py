from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator
from django.utils import timezone

from exam.models import ExamModule


class McqMaterial(models.Model):
    """
    MCQ听力材料实体类（一段材料可以对应多个问题）
    """
    # 材料标题
    title = models.CharField(
        max_length=200,
        null=False,
        blank=True,  # 允许为空，如果为空则自动从音频文件名获取
        verbose_name='材料标题',
        help_text='留空则自动使用音频文件名，例如：机场天气广播、空中交通对话等'
    )
    
    # 材料描述/场景说明
    description = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name='材料描述',
        help_text='材料的背景说明或场景描述'
    )
    
    # 音频ID (ManyToOne)
    audio_asset = models.ForeignKey(
        'media.MediaAsset',
        on_delete=models.SET_NULL,  # 删除媒体文件时，将此字段设为NULL，而不是阻止删除
        db_column='audio_id',
        null=True,  # 允许为空
        blank=True,  # 表单中允许为空
        related_name='mcq_materials',
        verbose_name='关联音频资源',
        help_text='听力材料的音频文件'
    )
    
    # 材料内容/文本（可选）
    content = models.TextField(
        null=True,
        blank=True,
        verbose_name='材料文本内容',
        help_text='听力材料的文字稿（可选）'
    )
    
    # 难度级别（可选）
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', '简单'),
            ('medium', '中等'),
            ('hard', '困难'),
        ],
        default='medium',
        verbose_name='难度级别'
    )
    
    # 显示顺序
    display_order = models.IntegerField(
        default=0,
        verbose_name='显示顺序',
        help_text='数字越小越靠前'
    )
    
    # 是否启用
    is_enabled = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )
    
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'mcq_materials'
        verbose_name = '听力材料'
        verbose_name_plural = '听力材料'
        ordering = ['display_order', '-created_at']
    
    def save(self, *args, **kwargs):
        """保存时自动设置标题（如果为空）"""
        if not self.title:
            if self.audio_asset:
                # 从音频文件名提取标题
                import os
                if self.audio_asset.file:
                    # 获取文件名（不含路径）
                    filename = os.path.basename(self.audio_asset.file.name)
                    # 去掉扩展名
                    title_without_ext = os.path.splitext(filename)[0]
                    # 清理文件名（替换下划线和连字符为空格）
                    self.title = title_without_ext.replace('_', ' ').replace('-', ' ')
                elif self.audio_asset.title:
                    # 如果文件为空，使用音频资源的标题
                    self.title = self.audio_asset.title
                else:
                    # 音频资源没有文件和标题
                    self.title = f'听力材料 {timezone.now().strftime("%Y%m%d%H%M%S")}'
            else:
                # 没有音频资源时的备选方案
                self.title = f'听力材料 {timezone.now().strftime("%Y%m%d%H%M%S")}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title}"
    
    def question_count(self):
        """获取该材料下的问题数量"""
        return self.questions.count()
    question_count.short_description = '问题数量'


class McqQuestion(models.Model):
    """
    听力理解选择题实体类
    """
    # 关联听力材料（可选）
    material = models.ForeignKey(
        'McqMaterial',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        verbose_name='关联听力材料',
        help_text='如果题目属于某个材料，选择对应的材料'
    )
    
    # 模块ID (ManyToOne)
    exam_module = models.ManyToManyField(
        to='exam.ExamModule',
        related_name='module_mcq',
        db_column='module_id',
        blank=True,
        verbose_name='关联考试模块'
    )

    # 音频ID (ManyToOne) - 单个题目的音频（如果没有关联材料）
    audio_asset = models.ForeignKey(
        'media.MediaAsset',
        on_delete=models.SET_NULL,  # 删除媒体文件时，将此字段设为NULL，而不是阻止删除
        db_column='audio_id',
        null=True,
        blank=True,
        related_name='mcq_questions',
        verbose_name='题目音频资源',
        help_text='单独题目的音频（如果有关联材料，可留空使用材料音频）'
    )

    # 题干文本 (columnDefinition = "TEXT" 对应 Django TextField)
    text_stem = models.TextField(
        null=True,
        blank=True,
        verbose_name='题干文本'
    )

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name='创建时间')

    class Meta:
        db_table = 'mcq_questions'
        verbose_name = '听力选择题'
        verbose_name_plural = '听力选择题'

    def __str__(self):
        return f"MCQ Question {self.id}"
    
    def get_audio(self):
        """获取题目音频（优先使用材料音频）"""
        if self.material and self.material.audio_asset:
            return self.material.audio_asset
        return self.audio_asset
    
    def get_audio_url(self):
        """获取音频URL"""
        audio = self.get_audio()
        if audio:
            return audio.get_file_url()
        return None


class McqChoice(models.Model):
    """
    听力理解选择题选项实体类
    """

    # 关联的题目实体 (ManyToOne)
    question = models.ForeignKey(
        'McqQuestion',
        on_delete=models.CASCADE,  # 题目删除时，选项一起删除
        db_column='question_id',
        null=False,
        related_name='choices',
        verbose_name='关联题目'
    )

    # 选项标签 A/B/C/D
    label = models.CharField(
        max_length=1,
        null=False,
        blank=True,  # 允许为空，自动生成
        validators=[
            RegexValidator(regex=r'[ABCD]', message="选项标签必须是A、B、C、D中的一个")
        ],
        verbose_name='选项标签',
        help_text='自动生成A、B、C、D，也可手动指定'
    )

    # 选项内容 (columnDefinition = "TEXT" 对应 Django TextField)
    content = models.TextField(max_length=1000, null=False, verbose_name='选项内容')

    # 是否为正确答案
    is_correct = models.BooleanField(default=False, null=False, verbose_name='是否正确答案')

    class Meta:
        db_table = 'mcq_choices'
        verbose_name = '选择题选项'
        verbose_name_plural = '选择题选项'
        unique_together = ('question', 'label')
        ordering = ['label']

    def __str__(self):
        return f"{self.label}. {self.content[:50]}"
    
    def save(self, *args, **kwargs):
        """保存时自动生成label"""
        if not self.label:
            # 获取当前题目已有的选项标签
            existing_labels = McqChoice.objects.filter(
                question=self.question
            ).exclude(pk=self.pk).values_list('label', flat=True)
            
            # 自动分配未使用的标签
            labels = ['A', 'B', 'C', 'D']
            for label in labels:
                if label not in existing_labels:
                    self.label = label
                    break
            
            # 如果所有标签都被占用，使用第一个可用的
            if not self.label:
                self.label = 'A'
        
        super().save(*args, **kwargs)


class McqResponse(models.Model):
    """
    听力选择题作答记录实体类
    """
    MODE_CHOICES = [
        ('practice', '训练模式'),
        ('exam', '考试模式'),
    ]

    # 模块本身 属于哪个模块的答题 (ManyToMany)
    module = models.ManyToManyField(
        to='exam.ExamModule',
        related_name='module_mcq_response',
        db_column='module_id',
    )


    # 问题本体 (ManyToOne)
    question = models.ForeignKey(
        'McqQuestion',
        on_delete=models.CASCADE,
        db_column='question_id',
        related_name='responses',
        verbose_name='关联题目'
    )

    # 被选中的选项 (ManyToOne)
    selected_choice = models.ForeignKey(
        'McqChoice',
        on_delete=models.SET_NULL,  # 选项删除时，作答记录中的选项ID可置空
        db_column='selected_choice_id',
        null=True,  # 允许用户未选择任何选项
        related_name='responses',
        verbose_name='被选中的选项'
    )

    # 是否答对（可为 null，待判分）
    is_correct = models.BooleanField(null=True)
    

    user = models.ForeignKey(
        to='account.WxUser',
        on_delete=models.CASCADE,
        verbose_name='回答人'
    )
    
    # 模式类型：训练或考试
    mode_type = models.CharField(
        max_length=20,
        choices=MODE_CHOICES,
        default='practice',
        null=False,
        verbose_name='模式类型',
        help_text='训练模式或考试模式'
    )
    
    # 回答时间
    answered_at = models.DateTimeField(default=timezone.now, null=False)

    is_timeout = models.BooleanField(default=False, null=False)

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'mcq_responses'
        verbose_name = '选择题作答记录'
        verbose_name_plural = '选择题作答记录'


    def __str__(self):
        return f"Response {self.id} for Q{self.question_id}"