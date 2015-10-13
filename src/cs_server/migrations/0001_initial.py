# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('response', models.TextField()),
                ('timestamp', models.DateTimeField(verbose_name='time submmited')),
            ],
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('grade', models.FloatField()),
                ('feedback', models.TextField()),
                ('timestamp', models.DateTimeField(verbose_name='time submmited')),
                ('answer', models.ForeignKey(to='cs_server.Answer')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('text', models.TextField()),
                ('meta', models.BinaryField()),
                ('pub_date', models.DateTimeField(verbose_name='date published')),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('school_id', models.CharField(max_length=20)),
            ],
        ),
        migrations.AddField(
            model_name='grade',
            name='student',
            field=models.ForeignKey(to='cs_server.Student'),
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(to='cs_server.Question'),
        ),
        migrations.AddField(
            model_name='answer',
            name='student1',
            field=models.ForeignKey(to='cs_server.Student', related_name='student1'),
        ),
        migrations.AddField(
            model_name='answer',
            name='student2',
            field=models.ForeignKey(to='cs_server.Student', related_name='student2'),
        ),
    ]
