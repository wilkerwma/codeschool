# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cs_app', '0007_auto_20150908_1719'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionBase',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
            ],
        ),
        migrations.RenameField(
            model_name='question',
            old_name='text',
            new_name='description',
        ),
        migrations.RemoveField(
            model_name='question',
            name='id',
        ),
        migrations.AddField(
            model_name='question',
            name='questionbase_ptr',
            field=models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, to='cs_app.QuestionBase', default=None, serialize=False),
            preserve_default=False,
        ),
    ]
