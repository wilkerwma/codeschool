# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-31 22:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cs_questions', '0014_quizactivity_language'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question',
            old_name='title',
            new_name='name',
        ),
    ]
