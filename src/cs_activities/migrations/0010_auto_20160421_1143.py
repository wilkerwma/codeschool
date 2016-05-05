# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-21 14:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cs_activities', '0009_synccodeedititem_activity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='synccodeedititem',
            name='next',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prev', to='cs_activities.SyncCodeEditItem'),
        ),
    ]