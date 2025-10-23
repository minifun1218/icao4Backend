from django.db import models
from django.utils import timezone


def user_avatar_upload_path(instance, filename):
    """用户头像上传路径"""
    ext = filename.split('.')[-1]
    filename = f'avatar_{instance.id}_{timezone.now().strftime("%Y%m%d%H%M%S")}.{ext}'
    return f'avatars/{filename}'

class Role(models.Model):
    """
    角色实体类
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        null=False,
        verbose_name='角色名称'
    )

    description = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name='描述'
    )

    code = models.CharField(
        max_length=50,
        null=False,
        unique=True,  # 假设 code 也是唯一的
        verbose_name='角色编码'
    )

    status = models.SmallIntegerField(
        default=1,
        choices=((1, '激活'), (0, '禁用')),
        verbose_name='状态'
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
        db_table = 'roles'  #
        verbose_name = '角色'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    # 辅助方法：检查角色是否激活
    def is_active(self):
        """
        检查角色是否激活
        """
        return self.status == 1

class WxUser(models.Model):
    """
    用户实体类
    对应数据库表：users
    """
    openid = models.CharField(
        max_length=50,
        unique=True,
        null=False,
        verbose_name='微信用户唯一标识'
    )

    username = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name='用户名'
    )

    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='电话'
    )

    avatar = models.ImageField(
        upload_to=user_avatar_upload_path,
        null=True,
        blank=True,
        verbose_name='用户头像',
        help_text='支持jpg, jpeg, png, gif格式'
    )

    gender = models.SmallIntegerField(
        null=True,
        choices=((1, '男'), (2, '女'), (0, '未知')),
        verbose_name='性别'
    )

    birthday = models.DateField(
        null=True,
        blank=True,
        verbose_name='出生日期'
    )

    level = models.IntegerField(
        null=True,
        verbose_name='等级/级别'
    )

    location = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name='所在地'
    )

    join_date = models.DateField(
        null=False,
        default=timezone.now, # 默认设置为当前日期
        verbose_name='加入日期'
    )

    status = models.SmallIntegerField(
        default=1,
        choices=((1, '正常'), (0, '禁用')),
        verbose_name='用户状态'
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

    # 用于保存最后登录时间
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后登录时间'
    )
    class Meta:
        db_table = 'users' # 对应 @Table(name = "users")
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username or f"User_{self.id}"
    
    @property
    def is_authenticated(self):
        """
        用户是否已认证（总是返回True，因为这是已登录用户对象）
        """
        return True
    
    @property
    def is_anonymous(self):
        """
        用户是否匿名（总是返回False，因为这是已登录用户对象）
        """
        return False
    
    @property
    def is_active(self):
        """
        检查用户是否激活
        """
        return self.status == 1
    
    def get_avatar_url(self):
        """获取头像URL"""
        if self.avatar:
            return self.avatar.url
        return None


class UserLearningProgress(models.Model):
    """
    用户学习进度实体类
    保存用户在各个学习模块的进度快照
    """
    
    # 关联用户
    user = models.ForeignKey(
        'WxUser',
        on_delete=models.CASCADE,
        related_name='learning_progress',
        verbose_name='用户'
    )
    
    # MCQ模块进度
    mcq_total = models.IntegerField(default=0, verbose_name='MCQ总题数')
    mcq_completed = models.IntegerField(default=0, verbose_name='MCQ已完成题数')
    mcq_correct = models.IntegerField(default=0, verbose_name='MCQ正确题数')
    mcq_practice_count = models.IntegerField(default=0, verbose_name='MCQ训练次数')
    mcq_exam_count = models.IntegerField(default=0, verbose_name='MCQ考试次数')
    
    # LSA模块进度
    lsa_total = models.IntegerField(default=0, verbose_name='LSA总题数')
    lsa_completed = models.IntegerField(default=0, verbose_name='LSA已完成题数')
    lsa_practice_count = models.IntegerField(default=0, verbose_name='LSA训练次数')
    lsa_exam_count = models.IntegerField(default=0, verbose_name='LSA考试次数')
    
    # Story模块进度
    story_total = models.IntegerField(default=0, verbose_name='Story总题数')
    story_completed = models.IntegerField(default=0, verbose_name='Story已完成题数')
    story_avg_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name='Story平均分'
    )
    story_practice_count = models.IntegerField(default=0, verbose_name='Story训练次数')
    story_exam_count = models.IntegerField(default=0, verbose_name='Story考试次数')
    
    # OPI模块进度
    opi_total = models.IntegerField(default=0, verbose_name='OPI总题数')
    opi_completed = models.IntegerField(default=0, verbose_name='OPI已完成题数')
    opi_avg_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name='OPI平均分'
    )
    opi_practice_count = models.IntegerField(default=0, verbose_name='OPI训练次数')
    opi_exam_count = models.IntegerField(default=0, verbose_name='OPI考试次数')
    
    # ATC模块进度
    atc_total = models.IntegerField(default=0, verbose_name='ATC总轮次数')
    atc_completed = models.IntegerField(default=0, verbose_name='ATC已完成轮次数')
    atc_avg_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name='ATC平均分'
    )
    atc_practice_count = models.IntegerField(default=0, verbose_name='ATC训练次数')
    atc_exam_count = models.IntegerField(default=0, verbose_name='ATC考试次数')
    
    # 总体统计
    total_study_time = models.IntegerField(default=0, verbose_name='总学习时长(分钟)')
    total_practice_count = models.IntegerField(default=0, verbose_name='总训练次数')
    total_exam_count = models.IntegerField(default=0, verbose_name='总考试次数')
    
    # 连续学习天数
    continuous_days = models.IntegerField(default=0, verbose_name='连续学习天数')
    last_study_date = models.DateField(null=True, blank=True, verbose_name='最后学习日期')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'user_learning_progress'
        verbose_name = '用户学习进度'
        verbose_name_plural = '用户学习进度'
        ordering = ['-updated_at']
        # 每个用户只有一条进度记录
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_progress')
        ]
    
    def __str__(self):
        return f"{self.user.username}的学习进度"
    
    def get_overall_progress(self):
        """计算总体进度百分比"""
        total = self.mcq_total + self.lsa_total + self.story_total + self.opi_total + self.atc_total
        completed = self.mcq_completed + self.lsa_completed + self.story_completed + self.opi_completed + self.atc_completed
        return round((completed / total * 100) if total > 0 else 0, 2)
    
    def get_mcq_accuracy(self):
        """计算MCQ正确率"""
        return round((self.mcq_correct / self.mcq_practice_count * 100) if self.mcq_practice_count > 0 else 0, 2)
    
    def update_continuous_days(self):
        """更新连续学习天数"""
        today = timezone.now().date()
        if self.last_study_date:
            if self.last_study_date == today:
                # 今天已经学习过了，不更新
                return
            elif (today - self.last_study_date).days == 1:
                # 昨天学习过，连续天数+1
                self.continuous_days += 1
            else:
                # 中断了，重新开始
                self.continuous_days = 1
        else:
            # 第一次学习
            self.continuous_days = 1
        
        self.last_study_date = today
        self.save()
