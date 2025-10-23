from django.db import models


class AvTermsTopic(models.Model):
    """
    航空术语主题分类实体类

    支持层级结构的主题分类管理
    """

    # 主题代码
    code = models.CharField(max_length=100, unique=True, null=False)

    # 中文名称
    name_zh = models.CharField(max_length=200, null=False)

    # 英文名称
    name_en = models.CharField(max_length=200, null=True, blank=True)

    # 主题描述 (Java columnDefinition="TEXT" 对应 Django TextField)
    description = models.TextField(max_length=5000, null=True, blank=True)

    # 显示顺序
    display_order = models.IntegerField(default=0, null=False)

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'av_terms_topics'
        verbose_name = '航空术语主题'
        verbose_name_plural = '航空术语主题'

        # 按照顺序和ID排序，对应 JPA 的 @OrderBy
        ordering = ['display_order', 'id']

    def __str__(self):
        return self.name_zh


class AvTerm(models.Model):
    """
    航空术语/词汇实体类
    支持通用语言学字段和多媒体资源关联
    """
    CERF_LEVEL = [
        ('A', '初级'),
        ('B', '中级'),
        ('C', '高级'),
    ]

    # 词条/术语
    headword = models.CharField(max_length=200, null=False)

    # 国际音标
    ipa = models.CharField(max_length=100, null=True, blank=True)

    # 英文释义 (Java columnDefinition="TEXT" 对应 Django TextField)
    definition_en = models.TextField(max_length=5000, null=True, blank=True)

    # 中文释义/术语说明 (Java columnDefinition="TEXT" 对应 Django TextField)
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
        related_name='terms',
        verbose_name='发音音频'
    )

    # 关联主题 (ManyToOne)
    topic = models.ForeignKey(
        'AvTermsTopic',
        on_delete=models.SET_NULL,
        db_column='topic_id',
        null=True,
        blank=True,
        related_name='terms',
        verbose_name='所属主题'
    )

    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'av_terms'
        verbose_name = '航空术语'
        verbose_name_plural = '航空术语'


    def __str__(self):
        return self.headword
