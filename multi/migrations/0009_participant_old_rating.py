# Generated by Django 3.2.7 on 2022-08-17 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multi', '0008_game_need_to_recalc'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='old_rating',
            field=models.FloatField(default=1500.0, verbose_name='対戦前のレーティング'),
        ),
    ]
