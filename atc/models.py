from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Airport(models.Model):

    # 唯一标识机场，例如："ZUUU"（成都双流国际机场）。
    icao = models.CharField(
        max_length=8,
        unique=True,
        null=False,
        verbose_name="国际民航组织（ICAO）四字代码"
    )

    # 机场名称。
    name = models.CharField(
        max_length=200,
        null=False,
        verbose_name="机场名称"
    )

    # 机场所在城市。
    city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="机场所在城市"
    )

    # 机场所在国家。
    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="机场所在国家"
    )

    # 时区。
    # 例如："Asia/Shanghai"
    timezone = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="时区"
    )


    # 是否激活。
    # true: 激活, false: 未激活
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否激活"
    )

    # 实体创建时间。
    # 由数据库自动设置，不可更新。
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name="创建时间"
    )

    # 实体更新时间。
    # 由数据库自动更新。
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )

    class Meta:
        db_table = 'airports'
        verbose_name = '机场'
        verbose_name_plural = '机场'
        ordering = ['icao']

    def __str__(self):
        return f"{self.name} ({self.icao})"

class AtcScenario(models.Model):

    # 机场ID (外键关联Airport)
    airport = models.ForeignKey(
        'Airport', # 假设在同一个App中或使用具体的App名
        on_delete=models.PROTECT, # 保护关联对象，避免误删
        related_name='scenarios',
        verbose_name="机场"
    )

    # 模块ID
    module = models.ForeignKey(
        to='exam.ExamModule',
        on_delete=models.PROTECT,
        related_name='atc_scenarios',
        verbose_name="关联模块"
    )


    # 场景标题
    title = models.CharField(
        max_length=255,
        null=False,
        verbose_name="场景标题"
    )

    # 场景描述
    description = models.TextField(
        max_length=2000,
        null=True,
        blank=True,
        verbose_name="场景描述"
    )


    # 是否激活
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否激活"
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name="创建时间"
    )

    # 更新时间
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )
    class Meta:
        db_table = 'atc_scenarios'
        verbose_name = 'ATC场景'
        verbose_name_plural = 'ATC场景'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (ID: {self.id})"

class AtcTurn(models.Model):

    # 
    SPEAKER_TYPE_PILOT = 'pilot'
    SPEAKER_TYPE_CONTROLLER = 'controller'
    SPEAKER_TYPES = [
        (SPEAKER_TYPE_PILOT, '飞行员'),
        (SPEAKER_TYPE_CONTROLLER, '管制员'),
    ]


    # 场景ID (外键关联atc_scenarios表)
    scenario = models.ForeignKey(
        'AtcScenario',
        on_delete=models.CASCADE, # 轮次依赖于场景，场景删除时轮次也应删除
        related_name='turns',
        null=False,
        verbose_name="关联场景"
    )

    # 轮次序号
    turn_number = models.IntegerField(
        validators=[MinValueValidator(1, message="轮次序号必须大于0")],
        null=False,
        verbose_name="轮次序号"
    )

    # 说话者类型（pilot/controller）
    speaker_type = models.CharField(
        max_length=20,
        choices=SPEAKER_TYPES,
        null=False,
        verbose_name="说话者类型"
    )

    # 音频文件路径
    audio = models.ForeignKey(
        to='media.MediaAsset',
        on_delete=models.CASCADE,
        related_name='turns_audio',
    )

    # 是否激活
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否激活"
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name="创建时间"
    )

    # 更新时间
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )

    # 关联的回答记录
    class Meta:
        db_table = 'atc_turns'
        verbose_name = 'ATC轮次'
        verbose_name_plural = 'ATC轮次'
        unique_together = ('scenario', 'turn_number',) # 场景和轮次序号组合唯一
        ordering = ['scenario', 'turn_number']


    def __str__(self):
        return f"场景{self.scenario_id} - 轮次{self.turn_number} ({self.get_speaker_type_display()})"

class AtcTurnResponse(models.Model):
    MODE_CHOICES = [
        ('practice', '训练模式'),
        ('exam', '考试模式'),
    ]

    # 模块本身 属于哪个模块的答题 (ManyToMany)
    modules = models.ManyToManyField(
        to='exam.ExamModule',
        related_name='module_atc_response',
        db_column='module_id',
    )

    # 轮次ID（外键关联atc_turns表）
    atc_turn = models.ForeignKey(
        'AtcTurn',
        on_delete=models.CASCADE,
        related_name='responses',
        null=False,
        verbose_name="关联轮次"
    )

    # 用户ID（外键关联users表）
    # 使用字符串引用 'auth.User' 或自定义的 User 模型
    user = models.ForeignKey(
        'account.WxUser', # 假设关联 Django 默认的 User 模型
        on_delete=models.PROTECT,
        related_name='atc_turn_responses',
        null=False,
        verbose_name="用户"
    )

    # 音频文件路径
    audio_file_path = models.ForeignKey(
        to='media.MediaAsset',
        on_delete=models.CASCADE,
        verbose_name="音频文件路径"
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

    # 音频时长（秒）
    is_timeout = models.BooleanField(default=False)


    # 得分 (precision=5)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.0'), message="得分不能为负数")],
        verbose_name="得分"
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name="创建时间"
    )

    # 更新时间
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )

    class Meta:
        db_table = 'atc_turn_responses'
        verbose_name = 'ATC轮次回答'
        verbose_name_plural = 'ATC轮次回答'
        ordering = ['-created_at']

    def __str__(self):
        return f"回答ID:{self.id} - 轮次:{self.atc_turn_id} - 用户:{self.user_id}"