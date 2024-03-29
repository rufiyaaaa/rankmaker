# Generated by Django 3.2.7 on 2022-09-15 15:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('multi', '0013_alter_affiliation_team'),
    ]

    operations = [
        migrations.AlterField(
            model_name='affiliation',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='affl_team', to='multi.team', verbose_name='チーム'),
        ),
        migrations.AlterField(
            model_name='duel',
            name='loser',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='duel_los', to='multi.player', verbose_name='敗者'),
        ),
        migrations.AlterField(
            model_name='duel',
            name='winner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='duel_win', to='multi.player', verbose_name='勝者'),
        ),
        migrations.AlterField(
            model_name='participant',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participant_player', to='multi.player', verbose_name='player'),
        ),
        migrations.AlterField(
            model_name='rating',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='multi.player', verbose_name='プレイヤー'),
        ),
    ]
