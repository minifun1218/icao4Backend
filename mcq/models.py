from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator
from django.utils import timezone

from exam.models import ExamModule


class McqQuestion(models.Model):
    """
    听力理解选择题实体类
    """
    # 模块ID (ManyToOne)
    exam_module = models.ManyToManyField(
        to='exam.ExamModule',
        related_name='module_mcq',
        db_column='module_id',
        blank=True,
        verbose_name='关联考试模块'
    )

    # 音频ID (ManyToOne)
    audio_asset = models.ForeignKey(
        'media.MediaAsset',  # 假设关联 MediaAsset 实体
        on_delete=models.PROTECT,  # 音频资源重要，防止被误删
        db_column='audio_id',
        null=False,
        related_name='mcq_questions',
        verbose_name='关联音频资源'
    )

    # 题干文本 (columnDefinition = "TEXT" 对应 Django TextField)
    text_stem = models.TextField(null=True, blank=True)

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'mcq_questions'
        verbose_name = '听力选择题'
        verbose_name_plural = '听力选择题'

    def __str__(self):
        return f"MCQ Question {self.id}"


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
        validators=[
            RegexValidator(regex=r'[ABCD]', message="选项标签必须是A、B、C、D中的一个")
        ]
    )

    # 选项内容 (columnDefinition = "TEXT" 对应 Django TextField)
    content = models.TextField(max_length=1000, null=False)

    # 是否为正确答案
    is_correct = models.BooleanField(default=False, null=False)

    class Meta:
        db_table = 'mcq_choices'
        verbose_name = '选择题选项'
        verbose_name_plural = '选择题选项'
        unique_together = ('question', 'label')

    def __str__(self):
        return f"{self.label}. {self.content[:50]}"


class McqResponse(models.Model):
    """
    听力选择题作答记录实体类
    """
    MODE_CHOICES = [
        ('practice', '训练模式'),
        ('exam', '考试模式'),
    ]
    
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