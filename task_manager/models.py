from django.db import models
from django.contrib.auth.models import User

step_names = {
    3: '03-已上传数据',
    4: '04-正在解析变量',
    5: '05-已选定变量',
    6: '06-正在提取文本特征(BERT-3模型)',
    7: '07-正在进行主成分分析(PCA模型)',
    8: '08-已完成主成分分析',
    9: '09-正在降维',
    10: '10-已完成降维',
    11: '11-正在聚类',
    12: '12-已完成聚类',
    13: '13-正在生成舆情的时间序列',
    14: '14-数据处理完成',
    15: '15-正在进行Granger因果检验',
}


class Task(models.Model):
    name = models.CharField(max_length=64, verbose_name='名称')
    user = models.ForeignKey(User, models.CASCADE, verbose_name='用户')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    busy = models.BooleanField(default=False, verbose_name='繁忙')

    posts = models.FileField(upload_to='dataset', blank=True, null=True, verbose_name='帖子数据集')
    current_step = models.IntegerField(default=3, verbose_name='创建步骤')

    def __str__(self):
        return self.name

    def current_step_description(self):
        if self.current_step not in step_names.keys():
            return '00-未知流程'
        return step_names[self.current_step]

    class Meta:
        verbose_name = verbose_name_plural = '任务'


class Column(models.Model):
    task = models.ForeignKey(Task, models.CASCADE, verbose_name='任务')
    name = models.TextField(verbose_name='名称')
    is_datetime = models.BooleanField(default=False, verbose_name='时间?')
    is_user_id = models.BooleanField(default=False, verbose_name='用户编号?')
    is_interaction = models.BooleanField(default=False, verbose_name='互动指标?')
    is_text = models.BooleanField(default=False, verbose_name='正文?')

    def __str__(self):
        return self.task.name + '-' + self.name

    class Meta:
        verbose_name = verbose_name_plural = '列'


class AsyncErrorMessage(models.Model):
    user = models.ForeignKey(User, models.CASCADE, verbose_name='用户')
    task = models.ForeignKey(Task, models.CASCADE, verbose_name='任务')
    happened_time = models.DateTimeField(auto_now_add=True, verbose_name='发生时间')
    current_step = models.IntegerField(default=3, verbose_name='创建步骤')
    error_message = models.TextField(blank=True)

    def __str__(self):
        return self.task.name + '-' + self.happened_time.strftime('%Y-%m-%d-%H:%M:%s')

    def current_step_description(self):
        if self.current_step not in step_names.keys():
            return '00-未知流程'
        return step_names[self.current_step]

    class Meta:
        verbose_name = verbose_name_plural = '异步错误'
