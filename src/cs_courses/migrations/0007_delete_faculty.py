# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-08 16:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cs_courses', '0006_facultypage'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Faculty',
        ),
    ]
