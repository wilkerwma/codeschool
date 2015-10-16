# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cs_app', '0010_auto_20150909_0041'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionIO',
            fields=[
                ('questionbase_ptr', models.OneToOneField(serialize=False, primary_key=True, auto_created=True, parent_link=True, to='cs_app.QuestionBase')),
                ('correct_answer', models.TextField()),
                ('examples', models.TextField()),
            ],
            bases=('cs_app.questionbase',),
        ),
        migrations.RemoveField(
            model_name='question',
            name='questionbase_ptr',
        ),
        migrations.AlterField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(to='cs_app.QuestionIO'),
        ),
        migrations.DeleteModel(
            name='Question',
        ),
    ]
