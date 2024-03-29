# Generated by Django 3.2.7 on 2022-08-16 11:28

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('multi', '0006_auto_20220816_2027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='試合日時'),
        ),
        migrations.AlterField(
            model_name='game',
            name='last_modify',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='最終更新日'),
        ),
    ]
