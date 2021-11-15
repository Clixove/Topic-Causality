# Generated by Django 3.2.9 on 2021-11-14 03:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('task_manager', '0005_column_is_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='Influence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_max_scaler', models.FileField(blank=True, null=True, upload_to='intermediate', verbose_name='归一化模型')),
                ('influence_metric', models.FileField(blank=True, null=True, upload_to='intermediate', verbose_name='影响力指标')),
                ('influence_metric_figure', models.FileField(blank=True, null=True, upload_to='figure', verbose_name='影响力指标分布图')),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='task_manager.task', verbose_name='任务')),
            ],
            options={
                'verbose_name': '影响力评价',
                'verbose_name_plural': '影响力评价',
            },
        ),
        migrations.CreateModel(
            name='EventTimeSeriesGenerator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_points', models.IntegerField(default=200, verbose_name='时间采样数')),
                ('influence_shrink_ratio', models.IntegerField(default=1, verbose_name='影响力衰减系数')),
                ('user_list', models.FileField(blank=True, null=True, upload_to='intermediate', verbose_name='用户列表')),
                ('event_ts', models.FileField(blank=True, null=True, upload_to='intermediate', verbose_name='事件时间序列')),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='task_manager.task', verbose_name='任务')),
            ],
            options={
                'verbose_name': '事件时间序列生成',
                'verbose_name_plural': '事件时间序列生成',
            },
        ),
        migrations.CreateModel(
            name='DecompositionContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pca_model', models.FileField(blank=True, null=True, upload_to='intermediate', verbose_name='主成分分析模型')),
                ('pca_figure', models.FileField(blank=True, null=True, upload_to='figure', verbose_name='主成分图')),
                ('pca_x_upper_bound', models.IntegerField(blank=True, null=True, verbose_name='主成分图横轴上边界')),
                ('pca_x_lower_bound', models.IntegerField(blank=True, null=True, verbose_name='主成分图横轴下边界')),
                ('kept_dimension', models.IntegerField(blank=True, null=True, verbose_name='保留特征维度')),
                ('std_decomposed_content', models.FileField(blank=True, null=True, upload_to='intermediate', verbose_name='降维&标准化后的文本特征')),
                ('standard_scaler', models.FileField(blank=True, null=True, upload_to='intermediate', verbose_name='标准化模型')),
                ('knn_figure', models.FileField(blank=True, null=True, upload_to='figure', verbose_name='最近邻图')),
                ('dbscan_model', models.FileField(blank=True, null=True, upload_to='intermediate', verbose_name='DBSCAN模型')),
                ('eps', models.FloatField(blank=True, null=True, verbose_name='Epsilon')),
                ('class_labels', models.FileField(blank=True, null=True, upload_to='intermediate', verbose_name='类别标签')),
                ('class_num', models.IntegerField(blank=True, null=True, verbose_name='类别数')),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='task_manager.task', verbose_name='任务')),
            ],
            options={
                'verbose_name': '文本特征降维',
                'verbose_name_plural': '文本特征降维',
            },
        ),
    ]