# Generated by Django 3.2.7 on 2022-08-17 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multi', '0009_participant_old_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='rating_diff',
            field=models.FloatField(default=0.0, verbose_name='レーティング変化'),
        ),
    ]