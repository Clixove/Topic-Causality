from django.db import models
from task_manager.models import Task


class GrangerCausality(models.Model):
    task = models.OneToOneField(Task, models.CASCADE, verbose_name='任务')
    max_lag = models.IntegerField(verbose_name='最大滞后阶', blank=True, null=True)
    current_event = models.IntegerField(verbose_name='当前事件', blank=True, null=True)
    current_user = models.TextField(verbose_name='当前用户', blank=True)
    direction = models.BooleanField(verbose_name='因果方向(是否主动方?)', default=True)

    def __str__(self):
        return self.task.name

    class Meta:
        verbose_name = verbose_name_plural = 'Granger因果'
