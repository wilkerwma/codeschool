# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cs_server', '0008_auto_20150909_0038'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question',
            old_name='correct',
            new_name='correct_answer',
        ),
        migrations.RemoveField(
            model_name='question',
            name='grader',
        ),
        migrations.RemoveField(
            model_name='question',
            name='include',
        ),
    ]
