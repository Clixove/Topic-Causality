# Generated by Django 3.2.4 on 2021-11-12 05:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_manager', '0004_column_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='column',
            name='is_text',
            field=models.BooleanField(default=False, verbose_name='正文?'),
        ),
    ]
