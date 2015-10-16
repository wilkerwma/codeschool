# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cs_app', '0004_auto_20150903_1921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='student2',
            field=models.ForeignKey(blank=True, to='cs_app.Student', related_name='student2', null=True),
        ),
        migrations.AlterField(
            model_name='answer',
            name='timestamp',
            field=models.DateTimeField(verbose_name='time submmited', auto_now_add=True),
        ),
        migrations.AlterUniqueTogether(
            name='student',
            unique_together=set([('name', 'school_id')]),
        ),
    ]
