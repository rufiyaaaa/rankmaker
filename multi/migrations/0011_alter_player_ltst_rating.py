# Generated by Django 3.2.7 on 2022-08-17 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multi', '0010_participant_rating_diff'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='ltst_rating',
            field=models.FloatField(default=0, verbose_name='最新レーティング'),
        ),
    ]
