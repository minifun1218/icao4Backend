from django.core.validators import MinValueValidator
from django.db import models

class AvVocabTopic(models.Model):
    """
    航空词汇主题分类实体类
    """

    # 主题代码 (Java @Column(unique = true))
    code = models.CharField(max_length=100, unique=True, null=False)

    # 中文名称
    name_zh = models.CharField(max_length=200, null=False)

    # 英文名称
    name_en = models.CharField(max_length=200, null=True, blank=True)

    # 主题描述（可选） (Java columnDefinition="TEXT" 对应 Django TextField)
    description = models.TextField(max_length=5000, null=True, blank=True)

    # 显示顺序
    display_order = models.IntegerField(default=0, null=False)

    # 创建时间 (Java @CreationTimestamp)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'av_vocab_topics'
        verbose_name = '航空词汇主题'
        verbose_name_plural = '航空词汇主题'

        # 按照顺序和ID排序
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.name_zh


class AvVocab(models.Model):
    """
    航空词汇实体类
    对应数据库表：av_vocabs
    支持通用语言学字段和多媒体资源关联
    """

    CERF_LEVEL = [
        ('A', '初级'),
        ('B', '中级'),
        ('C', '高级'),
    ]

    # 词条/术语
    headword = models.CharField(max_length=200, null=False)

    # 词形还原
    lemma = models.CharField(max_length=200, null=True, blank=True)

    # 词性
    pos = models.CharField(max_length=50, null=True, blank=True)

    # 国际音标
    ipa = models.CharField(max_length=100, null=True, blank=True)


    # 中文释义/词汇说明 (Java columnDefinition="TEXT" 对应 Django TextField)
    definition_zh = models.TextField(max_length=5000, null=True, blank=True)

    # 英文例句 (Java columnDefinition="TEXT" 对应 Django TextField)
    example_en = models.TextField(max_length=2000, null=True, blank=True)

    # 例句中文翻译 (Java columnDefinition="TEXT" 对应 Django TextField)
    example_zh = models.TextField(max_length=2000, null=True, blank=True)

    # CEFR等级
    cefr_level = models.CharField(
        max_length=2,
        choices=CERF_LEVEL,
        null=True,
        blank=True
    )

    # 发音音频资源 (ManyToOne)
    audio_asset = models.ForeignKey(
        'media.MediaAsset',  # 假设关联 MediaAsset 实体
        on_delete=models.SET_NULL,
        db_column='audio_asset_id',
        null=True,
        blank=True,
        related_name='vocabs',
        verbose_name='发音音频'
    )

    # 关联主题 (ManyToOne)
    topic = models.ForeignKey(
        'AvVocabTopic',
        on_delete=models.SET_NULL,
        db_column='topic_id',
        null=True,
        blank=True,
        related_name='vocabs',
        verbose_name='所属主题'
    )

    # 创建时间 (Java @CreationTimestamp)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'av_vocabs'
        verbose_name = '航空词汇'
        verbose_name_plural = '航空词汇'

    def __str__(self):
        return self.headword


class UserVocabLearning(models.Model):
    """
    用户词汇学习记录
    记录用户学习词汇的历史和进度
    """
    
    MASTERY_LEVEL_CHOICES = [
        (0, '未掌握'),
        (1, '初步了解'),
        (2, '基本掌握'),
        (3, '熟练掌握'),
        (4, '完全掌握'),
    ]
    
    # 关联用户
    user = models.ForeignKey(
        'account.WxUser',
        on_delete=models.CASCADE,
        related_name='vocab_learnings',
        verbose_name='用户'
    )
    
    # 关联词汇
    vocab = models.ForeignKey(
        'AvVocab',
        on_delete=models.CASCADE,
        related_name='user_learnings',
        verbose_name='词汇'
    )
    
    # 学习次数
    study_count = models.IntegerField(
        default=1,
        verbose_name='学习次数'
    )
    
    # 掌握程度
    mastery_level = models.IntegerField(
        choices=MASTERY_LEVEL_CHOICES,
        default=1,
        verbose_name='掌握程度'
    )
    
    # 是否收藏
    is_favorited = models.BooleanField(
        default=False,
        verbose_name='是否收藏'
    )
    
    # 是否标记为已掌握
    is_mastered = models.BooleanField(
        default=False,
        verbose_name='是否已掌握'
    )
    
    # 首次学习时间
    first_learned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='首次学习时间'
    )
    
    # 最后学习时间
    last_learned_at = models.DateTimeField(
        auto_now=True,
        verbose_name='最后学习时间'
    )
    
    # 下次复习时间（间隔重复算法）
    next_review_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='下次复习时间'
    )
    
    # 备注
    notes = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name='学习备注'
    )
    
    class Meta:
        db_table = 'user_vocab_learning'
        verbose_name = '用户词汇学习记录'
        verbose_name_plural = '用户词汇学习记录'
        ordering = ['-last_learned_at']
        # 一个用户对一个词汇只有一条学习记录
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'vocab'],
                name='unique_user_vocab_learning'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-last_learned_at']),
            models.Index(fields=['user', 'is_favorited']),
            models.Index(fields=['user', 'is_mastered']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.vocab.headword}"
    
    def increment_study_count(self):
        """增加学习次数"""
        from django.utils import timezone
        self.study_count += 1
        self.last_learned_at = timezone.now()
        self.save()


class UserTermLearning(models.Model):
    """
    用户术语学习记录
    记录用户学习术语的历史和进度
    """
    
    MASTERY_LEVEL_CHOICES = [
        (0, '未掌握'),
        (1, '初步了解'),
        (2, '基本掌握'),
        (3, '熟练掌握'),
        (4, '完全掌握'),
    ]
    
    # 关联用户
    user = models.ForeignKey(
        'account.WxUser',
        on_delete=models.CASCADE,
        related_name='term_learnings',
        verbose_name='用户'
    )
    
    # 关联术语
    term = models.ForeignKey(
        'term.AvTerm',
        on_delete=models.CASCADE,
        related_name='user_learnings',
        verbose_name='术语'
    )
    
    # 学习次数
    study_count = models.IntegerField(
        default=1,
        verbose_name='学习次数'
    )
    
    # 掌握程度
    mastery_level = models.IntegerField(
        choices=MASTERY_LEVEL_CHOICES,
        default=1,
        verbose_name='掌握程度'
    )
    
    # 是否收藏
    is_favorited = models.BooleanField(
        default=False,
        verbose_name='是否收藏'
    )
    
    # 是否标记为已掌握
    is_mastered = models.BooleanField(
        default=False,
        verbose_name='是否已掌握'
    )
    
    # 首次学习时间
    first_learned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='首次学习时间'
    )
    
    # 最后学习时间
    last_learned_at = models.DateTimeField(
        auto_now=True,
        verbose_name='最后学习时间'
    )
    
    # 下次复习时间
    next_review_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='下次复习时间'
    )
    
    # 备注
    notes = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
        verbose_name='学习备注'
    )
    
    class Meta:
        db_table = 'user_term_learning'
        verbose_name = '用户术语学习记录'
        verbose_name_plural = '用户术语学习记录'
        ordering = ['-last_learned_at']
        # 一个用户对一个术语只有一条学习记录
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'term'],
                name='unique_user_term_learning'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-last_learned_at']),
            models.Index(fields=['user', 'is_favorited']),
            models.Index(fields=['user', 'is_mastered']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.term.headword}"
    
    def increment_study_count(self):
        """增加学习次数"""
        from django.utils import timezone
        self.study_count += 1
        self.last_learned_at = timezone.now()
        self.save()