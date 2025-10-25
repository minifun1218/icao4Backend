from django.db import models
from django.utils import timezone


class ExamPaper(models.Model):
    """
    考试试卷实体类，
    """
    # 试卷代码，唯一且非空
    code = models.CharField(max_length=100, unique=True, null=False)

    # 试卷名称，非空
    name = models.CharField(max_length=200, null=False)

    # 总时长（分钟），非空
    total_duration_min = models.IntegerField(null=False)

    # 描述
    description = models.TextField(null=True, blank=True)

    # 创建时间，自动设置
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        db_table = 'exam_paper'
        verbose_name = '考试试卷'
        verbose_name_plural = '考试试卷'

    def __str__(self):
        return self.name

class ExamModule(models.Model):
    """
    考试模块实体类，用于定义试卷中的一个组成部分，如听力、口语等。
    """

    MODULE_TYPE = [
        ('LISTENING_MCQ', '听力理解'),
        ('STORY_RETELL', '故事复述'),
        ('LISTENING_SA', '听力简答题'),
        ('ATC_SIM', '模拟通话'),
        ('OPI', '口语面试'),
    ]

    # 关联的考试试卷（可选）
    exam_paper = models.ManyToManyField(
        ExamPaper,
        'exam_paper_module',
        db_column='exam_paper_id',
        blank=True,
        verbose_name='关联的考试试卷',
        help_text='可选：将此模块关联到一个或多个试卷'
    )
    title = models.CharField(max_length=200, null=False, default='',
                             verbose_name='题目备注')
    # 模块类型，使用枚举（TextChoices）存储，非空
    module_type = models.CharField(
        max_length=50,
        choices=MODULE_TYPE,
        null=False
    )
    # 模块在试卷中的显示顺序，可选
    display_order = models.IntegerField(
        null=True,
        blank=True,
        default=0,
        verbose_name='显示顺序',
        help_text='数字越小越靠前，留空默认为0'
    )

    # 得分
    score = models.IntegerField(null=True, blank=True)

    # 模块创建时间，自动设置，不可更新
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    # 激活状态，非空
    is_activate = models.BooleanField(default=True, null=False)

    # 模块考试时间（时长），可选，单位：毫秒
    duration = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='时长(毫秒)',
        help_text='考试时长，单位：毫秒（例如：10分钟 = 600000）'
    )

    class Meta:
        db_table = 'exam_modules'
        verbose_name = '试题模块'
        verbose_name_plural = '试题模块'


    def __str__(self):
        # exam_paper 是多对多字段，不能直接访问 .name
        papers = self.exam_paper.all()
        if papers.exists():
            paper_name = papers.first().name
            return f"{paper_name} - {self.get_module_type_display()} ({self.display_order or 0})"
        return f"{self.title or self.get_module_type_display()} ({self.display_order or 0})"

