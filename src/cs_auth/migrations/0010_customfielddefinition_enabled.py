# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-12 00:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cs_auth', '0009_auto_20160411_2150'),
    ]

    operations = [
        migrations.AddField(
            model_name='customfielddefinition',
            name='enabled',
            field=models.BooleanField(default=True, help_text='Enable or disable a custom field', verbose_name='enabled'),
        ),
    ]
