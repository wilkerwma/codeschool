# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cs_app', '0006_answer_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='short_description',
            field=models.CharField(default='', max_length=400),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='answer',
            name='student1',
            field=models.ForeignKey(to='cs_app.Student', related_name='answer_first'),
        ),
        migrations.AlterField(
            model_name='answer',
            name='student2',
            field=models.ForeignKey(to='cs_app.Student', related_name='answer_second', null=True, blank=True),
        ),
    ]
