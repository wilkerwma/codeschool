# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('cs_app', '0009_auto_20150909_0039'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='description',
        ),
        migrations.RemoveField(
            model_name='question',
            name='pub_date',
        ),
        migrations.RemoveField(
            model_name='question',
            name='short_description',
        ),
        migrations.RemoveField(
            model_name='question',
            name='title',
        ),
        migrations.AddField(
            model_name='questionbase',
            name='description',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='questionbase',
            name='pub_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 9, 9, 0, 41, 23, 795469, tzinfo=utc), verbose_name='date published', auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='questionbase',
            name='short_description',
            field=models.CharField(default='', max_length=400),
        ),
        migrations.AddField(
            model_name='questionbase',
            name='title',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
