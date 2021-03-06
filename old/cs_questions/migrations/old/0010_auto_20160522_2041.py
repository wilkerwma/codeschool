# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-22 23:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cs_activities', '0006_auto_20160511_1209'),
        ('cs_questions', '0009_auto_20160522_1302'),
    ]

    operations = [
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('activity_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='cs_activities.Activity')),
                ('grading_method', models.IntegerField(choices=[(0, 'largest grade of all responses'), (1, 'smallest grade of all responses'), (2, 'mean grade')])),
            ],
            options={
                'abstract': False,
            },
            bases=('cs_activities.activity',),
        ),
        migrations.CreateModel(
            name='QuizItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.PositiveIntegerField()),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cs_questions.QuestionActivity')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cs_questions.QuizActivity')),
            ],
        ),
        migrations.CreateModel(
            name='QuizResponse',
            fields=[
                ('response_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='cs_activities.Response')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cs_questions.QuizActivity')),
            ],
            options={
                'abstract': False,
            },
            bases=('cs_activities.response',),
        ),
        migrations.AlterField(
            model_name='freeanswerquestion',
            name='data_type',
            field=models.CharField(choices=[('file', 'Arbitrary file'), ('image', 'Image file'), ('pdf', 'PDF file'), ('richtext', 'Rich text input'), ('richtext', 'Plain text input')], max_length=10),
        ),
        migrations.AlterUniqueTogether(
            name='quizactivityitem',
            unique_together=set([('quiz', 'index')]),
        ),
    ]
