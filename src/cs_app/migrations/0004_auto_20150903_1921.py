# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cs_app', '0003_question_examples'),
    ]

    operations = [
        migrations.RenameField(
            model_name='grade',
            old_name='grade',
            new_name='value',
        ),
        migrations.AddField(
            model_name='question',
            name='correct',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='question',
            name='include',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
