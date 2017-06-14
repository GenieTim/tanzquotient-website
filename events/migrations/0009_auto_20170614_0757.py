# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-14 07:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0008_auto_20160905_1307'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='room',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='events', to='courses.Room'),
        ),
    ]
