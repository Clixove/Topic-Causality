from django.db import models
from task_manager.models import Task


class DecompositionContent(models.Model):
    task = models.OneToOneField(Task, models.CASCADE, verbose_name='任务')
    # 1. figure feature importance
    pca_model = models.FileField(upload_to='intermediate', verbose_name='主成分分析模型', blank=True, null=True)
    pca_figure = models.FileField(upload_to='figure', verbose_name='解释方差比率图', blank=True, null=True)
    # 2. KNN deciding minPts parameters
    kept_dimension = models.IntegerField(verbose_name='保留特征维度', blank=True, null=True)
    std_decomposed_content = models.FileField(
        upload_to='intermediate', verbose_name='降维&标准化后的文本特征', blank=True, null=True)
    standard_scaler = models.FileField(upload_to='intermediate', verbose_name='标准化模型', blank=True, null=True)
    knn_figure = models.FileField(upload_to='figure', verbose_name='最近邻图', blank=True, null=True)
    # 3. Calc topics via DBSCAN
    dbscan_model = models.FileField(upload_to='intermediate', verbose_name='DBSCAN模型', blank=True, null=True)
    eps = models.FloatField(verbose_name='Epsilon', blank=True, null=True)
    class_labels = models.FileField(upload_to='intermediate', verbose_name='类别标签', blank=True, null=True)
    class_num = models.IntegerField(verbose_name='类别数', blank=True, null=True)
    clusters_detail = models.TextField(verbose_name='类别详细', blank=True)

    def __str__(self):
        return self.task.name

    class Meta:
        verbose_name = verbose_name_plural = '文本特征降维'


class Influence(models.Model):
    task = models.OneToOneField(Task, models.CASCADE, verbose_name='任务')
    # 1. Zipping
    min_max_scaler = models.FileField(upload_to='intermediate', verbose_name='归一化模型', blank=True, null=True)
    # 2. weighting via information entropy
    influence_metric = models.FileField(upload_to='intermediate', verbose_name='影响力指标', blank=True, null=True)
    # 3. Influence metrics distribution
    influence_metric_figure = models.FileField(upload_to='figure', verbose_name='影响力指标分布图', blank=True, null=True)

    def __str__(self):
        return self.task.name

    class Meta:
        verbose_name = verbose_name_plural = '影响力评价'


class EventTimeSeriesGenerator(models.Model):
    task = models.OneToOneField(Task, models.CASCADE, verbose_name='任务')
    time_points = models.IntegerField(default=200, verbose_name='时间采样数')
    influence_shrink_ratio = models.IntegerField(default=1, verbose_name='影响力衰减系数')
    user_list = models.FileField(upload_to='intermediate', verbose_name='用户列表', blank=True, null=True)
    event_ts = models.FileField(upload_to='intermediate', verbose_name='事件时间序列', blank=True, null=True)

    def __str__(self):
        return self.task.name

    class Meta:
        verbose_name = verbose_name_plural = '事件时间序列生成'
