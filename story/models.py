from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from exam.models import ExamModule
from media.models import MediaAsset
class RetellItem(models.Model):
    """
    复述题目实体类

    修改说明：将与 ExamModule 的关系从多对一改为多对多。
    """

    # 关联模块 (多对多关系)
    exam_modules = models.ManyToManyField(
        'exam.ExamModule',  # 假设关联 ExamModule 实体
        related_name='retell_items',
        verbose_name='关联考试模块'
    )

    # 题目标题
    title = models.CharField(max_length=200, null=False)

    # 音频资源 (ManyToOne)
    audio_asset = models.ForeignKey(
        'media.MediaAsset',  # 假设关联 MediaAsset 实体
        on_delete=models.PROTECT,
        db_column='audio_asset_id',
        null=False,
        related_name='retell_items',
        verbose_name='音频资源'
    )

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'retell_items'
        verbose_name = '复述题目'
        verbose_name_plural = '复述题目'

    def __str__(self):
        return self.title

class RetellResponse(models.Model):
    """
    复述回答实体类
    对应数据库表：retell_responses
    """
    MODE_CHOICES = [
        ('practice', '训练模式'),
        ('exam', '考试模式'),
    ]

    # 关联复述题目 (ManyToOne)
    retell_item = models.ForeignKey(
        'RetellItem',
        on_delete=models.CASCADE, # 题目删除时，回答一起删除
        db_column='item_id',
        null=False,
        related_name='responses',
        verbose_name='关联复述题目'
    )

    # 回答音频资源 (ManyToOne)
    answer_audio = models.ForeignKey(
        'media.MediaAsset',
        on_delete=models.SET_NULL, # 音频删除时，回答记录中的音频ID可置空
        db_column='answer_audio_id',
        null=True,
        blank=True,
        related_name='retell_responses',
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

    # 回答时间
    answered_at = models.DateTimeField(default=timezone.now, null=False)

    is_timeout = models.BooleanField(null=False, blank=False, default=False)

    # 得分 (Java BigDecimal/precision=6)
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'retell_responses'
        verbose_name = '复述回答'
        verbose_name_plural = '复述回答'

    def __str__(self):
        return f"Response for Item {self.retell_item_id}"