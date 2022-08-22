# Generated by Django 3.2.7 on 2022-08-16 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multi', '0004_team_one_on_one'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='one_on_one',
            field=models.BooleanField(blank=True, default=False, help_text='対戦結果登録時に使用したい入力方式を選択できます', verbose_name='入力方式'),
        ),
    ]