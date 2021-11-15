import io

import numpy as np
import pandas as pd
from django.db import models
from task_manager.models import Task
import matplotlib.pyplot as plt


class DescriptiveStatistics(models.Model):
    task = models.OneToOneField(Task, models.CASCADE)
    time_trending = models.FileField(upload_to='figure', verbose_name="时间发帖趋势", blank=True, null=True)
    user_trending = models.FileField(upload_to='figure', verbose_name="用户发帖趋势", blank=True, null=True)

    def __str__(self):
        return self.task.name

    class Meta:
        verbose_name = verbose_name_plural = '描述性统计'


def draw_descriptive_statistics_figures(posts: pd.DataFrame, name_user_id: str, name_datetime: str):
    f, fig1 = io.BytesIO(), plt.figure()
    daily_trending = {}
    posts[name_datetime] = posts[name_datetime].astype('datetime64')
    for date, sub_posts in posts.groupby([posts[name_datetime].dt.date]):
        daily_trending[date] = sub_posts.shape[0]
    plt.bar(daily_trending.keys(), height=daily_trending.values())
    plt.xticks(rotation=45)
    plt.subplots_adjust(bottom=0.25)
    plt.xlabel("Date")
    plt.ylabel("Number of Posts")
    fig1.savefig(f, format='png')
    plt.close(fig1)

    g = io.BytesIO()
    fig2, ax = plt.subplots()
    user_trending = []
    for _, sub_posts in posts.groupby(name_user_id):
        user_trending.append(sub_posts.shape[0])
    _, frequency = np.unique(user_trending, return_counts=True)
    frequency = np.sort(frequency)[::-1]
    plt.plot(frequency)
    ax.set_yscale('log')
    plt.xlabel("Number of Posts Per User")
    plt.ylabel("Number of Users")
    fig2.savefig(g, format='png')
    plt.close(fig2)
    return f.getvalue(), g.getvalue()
