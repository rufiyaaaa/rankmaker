import logging
import os
import datetime


from django import forms

from .models import Game, Player, Affiliation, Team, Participant
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.timezone import make_aware


class PlayerCreateForm(forms.ModelForm):
    name = forms.CharField(label='名前', max_length=30)

    class Meta:
        model = Player
        fields = ('name', 'inactive')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BatchPlayerCreateForm(forms.ModelForm):
    name = forms.CharField(label='プレイヤー名', widget=forms.Textarea)

    class Meta:
        model = Player
        fields = ('name',)


class TeamCreateForm(forms.ModelForm):
    name = forms.CharField(label='チーム名', max_length=30)

    class Meta:
        model = Team
        fields = ('name', 'description')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class TeamConfigForm(forms.ModelForm):
    name = forms.CharField(label='チーム名', max_length=50, required=True)
    page_id = forms.CharField(
        label="キーフレーズ",
        max_length=20,
        required=False,
        help_text="ランキングをシェアする際の文字列を設定します。<br>5文字以上20文字以下の半角英数字で、他のチームですでに使用されている文字列は設定できません。"
    )

    class Meta:
        model = Team
        fields = ('name', 'description', 'page_id')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class GameCreateForm(forms.ModelForm):
    name = forms.CharField(label='試合タイトル', max_length=50, required=False)
    date = forms.DateTimeField(
        label='試合日時',
        required=True,
        initial=make_aware(datetime.datetime.now()),
        help_text='試合の前後を判断するのに用います。<br>「YYYY-MM-DD HH:MM」の形式で入力してください。'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial = kwargs.pop('initial')
        players = initial.pop('players')
        participants = initial.pop('initial_value')
        for player in players:
            self.fields[player.pk] = forms.IntegerField(
                label=player.name+"さんの順位",
                initial=None,
                required=False,
                validators=[MinValueValidator(1)]
            )
        for participant in participants:
            self.fields[participant.player.pk] = forms.IntegerField(
                label=participant.player.name+"さんの順位",
                initial=participant.rank,
                required=False,
                validators=[MinValueValidator(1)]
            )
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control align-middle'
        self.fields['date'].widget.attrs['id'] = 'datepicker'

    class Meta:
        model = Game
        fields = ('name', 'date')
        # widgets = {
        #     'date': DateTimePickerInput(
        #         format='%Y-%m-%d %H:%M:%S',
        #         options={
        #             'locale': 'ja',
        #             'dayViewHeaderFormat': 'YYYY年 MMMM',
        #         }
        #     )
        # }

    def is_valid(self):
        return super().is_valid()

    def clean(self):
        input_data = self.data

        try:
            date = make_aware(datetime.datetime.strptime(input_data['date'], '%Y-%m-%d %H:%M:%S'))
        except ValueError:
            raise ValidationError('日付の入力形式が間違っています')
        if not self.instance:
            if Game.objects.filter(date=date):
                raise ValidationError('同時に開催されている試合があるようです。時刻をずらしてください。')

        if date > make_aware(datetime.datetime.now()):
            raise ValidationError('未来の結果を入力することはできません')

        not_none = 0
        ranks = []
        for item in input_data.items():
            if item[0] != 'csrfmiddlewaretoken' and item[0] != 'name' and item[0] != 'date':
                if item[1] != '':
                    not_none += 1
                    ranks.append(int(item[1]))
                    if int(item[1]) <= 0:
                        raise ValidationError('順位は１以上の整数で入力してください')
        if not_none == 0 or not_none == 1:
            raise ValidationError('2名以上に順位を入力してください')
        ranks = sorted(ranks)
        memory = 1
        for i, rank in enumerate(ranks, 1):
            if i == rank or rank == memory:
                memory = rank
            else:
                raise ValidationError('同率順位の入力に問題があるようです')

        return input_data







