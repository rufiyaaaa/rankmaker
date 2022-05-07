# Generated by Django 3.2.7 on 2022-05-07 14:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('multi', '0005_auto_20220507_2327'),
    ]

    operations = [
        migrations.AlterField(
            model_name='affiliation',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='duel_affl_team', to='multi.team', verbose_name='チーム'),
        ),
        migrations.AlterField(
            model_name='affiliation',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='br_affl_user', to=settings.AUTH_USER_MODEL, verbose_name='ユーザー'),
        ),
        migrations.AlterField(
            model_name='duel',
            name='game',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='duel_game', to='multi.game', verbose_name='対応するGame'),
        ),
        migrations.AlterField(
            model_name='game',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='multi.team', verbose_name='チーム'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='game',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participant_game', to='multi.game', verbose_name='ゲーム'),
        ),
        migrations.AlterField(
            model_name='player',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='multi.team', verbose_name='所属'),
        ),
    ]
