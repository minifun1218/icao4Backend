from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from exam.models import ExamModule


class LsaDialog(models.Model):
    """
    听力简答对话实体类
    对应数据库表：lsa_dialogs
    """

    # 主键ID
    id = models.AutoField(primary_key=True)

    # 关联考试模块 (ManyToOne)
    exam_module = models.ManyToManyField(
        to='exam.ExamModule',
        related_name='module_lsa',
        db_column='module_id',
        verbose_name='关联考试模块'
    )

    # 对话标题
    title = models.CharField(max_length=255, null=False)

    # 对话描述
    description = models.TextField(null=True, blank=True)

    # 对话音频资源 (ManyToOne)
    audio_asset = models.ForeignKey(
        'media.MediaAsset',  # 假设资源实体名为 MediaAsset
        on_delete=models.SET_NULL,
        db_column='audio_id',
        null=True,
        blank=True,
        related_name='dialogs',
        verbose_name='对话音频资源'
    )

    # 显示顺序
    display_order = models.IntegerField(null=False)

    # 是否激活
    is_active = models.BooleanField(default=True, null=False)

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    # 更新时间
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lsa_dialogs'
        verbose_name = '听力理解对话'
        verbose_name_plural = '听力理解对话'

    def __str__(self):
        return self.title

class LsaQuestion(models.Model):
    """
    听力理解问题实体类
    对应数据库表：lsa_questions
    """

    # 对话ID (ManyToOne)
    dialog = models.ForeignKey(
        'LsaDialog',
        on_delete=models.CASCADE,
        db_column='dialog_id',
        related_name='questions',
        verbose_name='关联对话'
    )

    # 问题类型
    question_type = models.CharField(max_length=50, null=False)

    # 问题文本
    question_text = models.CharField(max_length=2000, null=False)

    # 选项A, B, C, D
    option_a = models.CharField(max_length=500, null=True, blank=True)
    option_b = models.CharField(max_length=500, null=True, blank=True)
    option_c = models.CharField(max_length=500, null=True, blank=True)
    option_d = models.CharField(max_length=500, null=True, blank=True)

    # 正确答案
    correct_answer = models.CharField(max_length=10, null=True, blank=True)

    # 答案解析
    answer_explanation = models.CharField(max_length=1000, null=True, blank=True)


    # 显示顺序
    display_order = models.IntegerField(
        null=True, # 字段本身允许null
        blank=True,
        validators=[MinValueValidator(1)]
    )




    # 是否激活
    is_active = models.BooleanField(default=True, null=False)

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    # 更新时间
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lsa_questions'
        verbose_name = '听力理解问题'
        verbose_name_plural = '听力理解问题'


    def __str__(self):
        return f"Q{self.id}: {self.question_text[:30]}..."


class LsaResponse(models.Model):
    """
    口语作答（录音）实体类
    对应表：lsa_responses
    """
    MODE_CHOICES = [
        ('practice', '训练模式'),
        ('exam', '考试模式'),
    ]

    # 外键：题目ID (ManyToOne)
    question = models.ForeignKey(
        'LsaQuestion',
        on_delete=models.CASCADE,
        db_column='question_id',
        related_name='responses',
        verbose_name='关联题目'
    )



    # 外键：学生作答录音ID (ManyToOne)
    answer_audio = models.ForeignKey(
        'media.MediaAsset',
        on_delete=models.SET_NULL,
        db_column='answer_audio_id',
        null=True,
        blank=True,
        related_name='responses',
        verbose_name='回答音频资源'
    )

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

    is_timeout = models.BooleanField(null=False, blank=False, default=False)

    # 作答时间点 (Java @PrePersist 逻辑，此处设置 default)
    answered_at = models.DateTimeField(default=timezone.now, null=False)


    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'lsa_responses'
        verbose_name = '口语作答'
        verbose_name_plural = '口语作答'


    def __str__(self):
        return f"Response for Q{self.question_id} in Attempt {self.attempt_id}"