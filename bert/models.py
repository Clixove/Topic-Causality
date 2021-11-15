from django.db import models
from task_manager.models import Task


class BERT(models.Model):
    task = models.OneToOneField(Task, models.CASCADE, verbose_name='任务')
    text_features = models.FileField(upload_to='intermediate', verbose_name='文本特征', blank=True, null=True)
