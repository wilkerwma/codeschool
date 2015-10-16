# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cs_app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='meta',
        ),
        migrations.AddField(
            model_name='question',
            name='grader',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
