# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-31 22:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cs_activities', '0006_auto_20160511_1209'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='long_description',
            field=models.TextField(blank=True, verbose_name='long description'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='name',
            field=models.CharField(max_length=140, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='short_description',
            field=models.TextField(default='no-description', verbose_name='short description'),
        ),
    ]
