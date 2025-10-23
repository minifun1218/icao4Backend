from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone


class OpiTopic(models.Model):
    """
    OPI（口语面试）话题实体类
    对应表：opi_topics
    """
    # 关联的考试模块 (ManyToOne)
    exam_module = models.ManyToManyField(
        to='exam.ExamModule',
        related_name='opi_topic',
        db_column='module_id',
        blank=True,
        verbose_name='所属模块'
    )

    # 话题顺序（与 module_id 联合唯一）
    order = models.IntegerField(null=False, db_column='t_order')

    # 话题标题
    title = models.CharField(max_length=200, null=False)

    # 话题描述（可选）
    description = models.TextField(null=True, blank=True)

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'opi_topics'
        verbose_name = 'OPI话题'
        verbose_name_plural = 'OPI话题'


    def __str__(self):
        return self.title


class OpiQuestion(models.Model):
    """
    OPI问题实体类
    对应数据库表：opi_questions
    """

    # 关联的话题 (ManyToOne)
    topic = models.ForeignKey(
        'OpiTopic',
        on_delete=models.CASCADE,
        db_column='topic_id',
        null=False,
        related_name='questions',
        verbose_name='关联话题'
    )

    # 问题顺序（与 topic_id 联合唯一）
    QOrder = models.IntegerField(
        null=False,
        db_column='q_order',
        validators=[MinValueValidator(1, message="问题顺序必须大于0")]
    )

    # 预录提问音频ID (ManyToOne)
    prompt_audio = models.ForeignKey(
        'media.MediaAsset',  # 假设关联 MediaAsset 实体
        on_delete=models.PROTECT,  # 音频资源重要，防止被误删
        db_column='prompt_audio_id',
        null=False,
        related_name='opi_questions',
        verbose_name='提问音频'
    )

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'opi_questions'
        verbose_name = 'OPI问题'
        verbose_name_plural = 'OPI问题'

    def __str__(self):
        return f"Topic {self.topic_id} - Q{self.QOrder}"


class OpiResponse(models.Model):
    """
    OPI回答实体类
    对应数据库表：opi_responses
    """
    MODE_CHOICES = [
        ('practice', '训练模式'),
        ('exam', '考试模式'),
    ]


    # 关联的问题 (ManyToOne)
    question = models.ForeignKey(
        'OpiQuestion',
        on_delete=models.CASCADE,
        db_column='question_id',
        null=False,
        related_name='responses',
        verbose_name='关联问题'
    )


    # 回答音频ID (ManyToOne)
    answer_audio = models.ForeignKey(
        'media.MediaAsset',  # 假设关联 MediaAsset 实体
        on_delete=models.SET_NULL,  # 音频删除时，回答记录中的音频ID可置空
        db_column='answer_audio_id',
        null=True,
        blank=True,
        related_name='opi_responses',
        verbose_name='回答音频'
    )

    # 回答时间
    answered_at = models.DateTimeField(default=timezone.now, null=False)

    # 评分 (Java BigDecimal/precision=6)
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
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
    
    # 是否超时
    is_timeout = models.BooleanField(null=False, blank=False, default=False)

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    class Meta:
        db_table = 'opi_responses'
        verbose_name = 'OPI回答'
        verbose_name_plural = 'OPI回答'
        constraints = [
            UniqueConstraint(fields=['question'], name='uk_question_only')
        ]

    def __str__(self):
        return f"Response for Q{self.question_id}"