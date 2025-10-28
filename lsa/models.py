from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from exam.models import ExamModule


class LsaDialog(models.Model):
    """
    听力简答对话实体类
    对应数据库表：lsa_dialogs
    """
    # 关联考试模块 (ManyToMany) - 可选
    exam_module = models.ManyToManyField(
        to='exam.ExamModule',
        related_name='module_lsa',
        db_column='module_id',
        blank=True,
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

    display_order = models.BigIntegerField(default=0, null=True,)
    # 是否激活
    is_active = models.BooleanField(default=True, null=False)

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    # 更新时间
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lsa_dialogs'
        verbose_name = '听力简答对话'
        verbose_name_plural = '听力简答对话'

    def __str__(self):
        return self.title

class LsaQuestion(models.Model):
    """
    听力理解问题实体类
    对应数据库表：lsa_questions
    """

    # 对话ID (ManyToMany)
    dialog = models.ManyToManyField(
        'LsaDialog',
        db_column='dialog_id',
        related_name='lsa_questions',
        blank=True,
        verbose_name='关联对话',
        help_text='可选择该问题所属的对话（可多选）'
    )


    # 问题文本
    question_text = models.CharField(
        max_length=2000, 
        null=False,
        verbose_name='题目文本',
        help_text='输入题目内容'
    )

    # 问题音频资源
    question_audio = models.ForeignKey(
        'media.MediaAsset',
        on_delete=models.SET_NULL,
        db_column='question_audio_id',
        null=True,
        blank=True,
        related_name='lsa_questions_audio',
        verbose_name='问题音频',
        help_text='上传问题音频文件'
    )

    # 显示顺序
    display_order = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='显示顺序',
        help_text='数字越小越靠前'
    )

    # 是否激活
    is_active = models.BooleanField(
        default=True, 
        null=False,
        verbose_name='是否激活',
        help_text='取消激活后该题目将不会显示'
    )

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    # 更新时间
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lsa_questions'
        verbose_name = '听力简答问题'
        verbose_name_plural = '听力简答问题'


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

    modules = models.ManyToManyField(
        to='exam.ExamModule',
        related_name='module_lsa_response',
        db_column='module_id',
    )


    # 外键：题目ID (ManyToOne)
    question = models.ForeignKey(
        'LsaQuestion',
        on_delete=models.CASCADE,
        db_column='question_id',
        related_name='lsa_responses',
        verbose_name='关联题目'
    )


    # 外键：学生作答录音ID (ManyToOne)
    answer_audio = models.ForeignKey(
        'media.MediaAsset',
        on_delete=models.SET_NULL,
        db_column='answer_audio_id',
        null=True,
        blank=True,
        related_name='lsa_responses_audio',
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
        verbose_name = '听力简单作答'
        verbose_name_plural = '听力简单作答'


    def __str__(self):
        return f"Response for Q{self.question_id} in Attempt {self.attempt_id}"