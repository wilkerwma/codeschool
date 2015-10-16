# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cs_app', '0002_auto_20150902_2216'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='examples',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
