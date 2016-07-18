# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-18 07:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscribers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriber',
            name='name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='send_hour',
            field=models.IntegerField(choices=[(12, '12:00 AM'), (1, '1:00 AM'), (2, '2:00 AM'), (3, '3:00 AM'), (4, '4:00 AM'), (5, '5:00 AM'), (6, '6:00 AM'), (7, '7:00 AM'), (8, '8:00 AM'), (9, '9:00 AM'), (10, '10:00 AM'), (11, '11:00 AM'), (12, '12:00 PM'), (1, '1:00 PM'), (2, '2:00 PM'), (3, '3:00 PM'), (4, '4:00 PM'), (5, '5:00 PM'), (6, '6:00 PM'), (7, '7:00 PM'), (8, '8:00 PM'), (9, '9:00 PM'), (10, '10:00 PM'), (11, '11:00 PM')], default=8),
        ),
    ]