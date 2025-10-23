from django.db import models
from django.utils import timezone
import os


def banner_image_upload_path(instance, filename):
    """Banner图片上传路径"""
    ext = filename.split('.')[-1]
    filename = f'banner_{instance.id}_{timezone.now().strftime("%Y%m%d%H%M%S")}.{ext}'
    return f'banners/{filename}'


class Banner(models.Model):
    """
    导播图组实体类
    对应数据库表：banners
    管理轮播图的分组，每个组可以包含多个轮播图项目
    """

    name = models.CharField(
        max_length=100,
        null=False,
        verbose_name='导播图组名称'
    )

    description = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='导播图组描述'
    )

    sort_order = models.IntegerField(
        default=0,
        verbose_name='排序权重'
    )

    is_active = models.BooleanField(
        default=True,
        null=False,
        verbose_name='是否启用'
    )

    start_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='开始显示时间'
    )

    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='结束显示时间'
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name='创建时间'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )


    class Meta:
        db_table = 'banners'  # 对应 @Table(name = "banners")
        verbose_name = '导播图组'
        verbose_name_plural = verbose_name

        # 默认排序，与 JPA 的 @OrderBy 保持一致 (sort_order 降序)
        ordering = ['-sort_order', 'created_at']

    def __str__(self):
        return self.name


    class BannerStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', '活跃 (正常显示中)'
        INACTIVE = 'INACTIVE', '未激活 (已禁用，不显示)'
        SCHEDULED = 'SCHEDULED', '定时 (等待开始时间)'
        EXPIRED = 'EXPIRED', '过期 (已过结束时间)'
        DRAFT = 'DRAFT', '草稿 (草稿状态，未发布)'

    def is_enabled(self):
        """检查是否启用"""
        return self.is_active

    def has_time_limit(self):
        """检查是否有时间限制"""
        return self.start_time is not None or self.end_time is not None

    def is_in_display_time(self):
        """检查当前时间是否在显示时间范围内"""
        now = timezone.now()

        # 检查开始时间
        if self.start_time and now < self.start_time:
            return False

        # 检查结束时间
        if self.end_time and now > self.end_time:
            return False

        return True

    def should_display(self):
        """检查是否应该显示（启用且在时间范围内）"""
        return self.is_enabled() and self.is_in_display_time()

    def get_current_status(self):
        """获取当前状态"""
        if not self.is_enabled():
            return self.BannerStatus.INACTIVE

        now = timezone.now()

        if self.start_time and now < self.start_time:
            return self.BannerStatus.SCHEDULED

        if self.end_time and now > self.end_time:
            return self.BannerStatus.EXPIRED

        return self.BannerStatus.ACTIVE

    def get_item_count(self):
        """获取导播图项目数量"""
        # 假设 BannerItem 的反向关联名为 'items'
        return self.banneritem_set.count()



    def get_remaining_display_minutes(self):
        """获取剩余显示时间（分钟）"""
        if not self.end_time or not self.is_in_display_time():
            return None

        # 确保时区一致性
        duration = self.end_time - timezone.now()
        if duration.total_seconds() > 0:
            return int(duration.total_seconds() // 60)
        return 0
class BannerItem(models.Model):
    """
    导播图项目实体类
    对应数据库表：banner_items
    """

    banner = models.ForeignKey(
        'Banner',  # 假设 Banner 模型名，如果不在同一文件需使用 'app_name.Banner'
        on_delete=models.CASCADE,
        db_column='banner_id',
        null=False,
        verbose_name='所属导播图组'
    )

    title = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name='图片标题'
    )

    description = models.TextField(
        max_length=1000,  # 约束字段最大长度
        null=True,
        blank=True,
        verbose_name='图片描述'
    )

    image = models.ImageField(
        upload_to=banner_image_upload_path,
        null=False,
        verbose_name='轮播图图片',
        help_text='支持jpg, jpeg, png, gif格式'
    )

    link_url = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='点击跳转链接'
    )

    sort_weight = models.IntegerField(
        default=0,
        null=False,
        verbose_name='排序权重'
    )

    is_enabled = models.BooleanField(
        default=True,
        null=False,
        verbose_name='是否启用'
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        verbose_name='创建时间'
    )

    # updated_at 对应 @UpdateTimestamp
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )

    class Meta:
        db_table = 'banner_items'  # 对应 @Table(name = "banner_items")
        verbose_name = '导播图项目'
        verbose_name_plural = verbose_name
        # 默认按排序权重降序排列
        ordering = ['-sort_weight', 'created_at']

    def __str__(self):
        return self.title or f'BannerItem {self.id}'
    
    def get_image_url(self):
        """获取图片URL"""
        if self.image:
            return self.image.url
        return None


