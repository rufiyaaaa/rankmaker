import logging
import os
import datetime

from dateutil import parser

from django import forms
from .models import Game, Player, Affiliation, Team, Participant
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils.timezone import make_aware


class PlayerCreateForm(forms.ModelForm):
    name = forms.CharField(label='名前', max_length=40)

    class Meta:
        model = Player
        fields = ('name', 'inactive')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BatchPlayerCreateForm(forms.ModelForm):
    name = forms.CharField(label='プレイヤー名', widget=forms.Textarea, max_length=10000)

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
    one_on_one = forms.ChoiceField(
        label='デフォルト入力方式',
        help_text='対戦結果登録時、初めに表示される入力方式を選択できます',
        choices=((True, '1対1対戦'), (False, '多人数対戦'))
    )
    offset_term = forms.ChoiceField(
        label='暫定レーティング期間',
        help_text='加入したばかりのプレイヤーには暫定レーティングが設定されます。暫定レーティングを適用する期間を設定してください。<br>この値を変更するとレーティングの再計算が必要になります。',
        choices=((20, '短め(約20対戦)'), (50, '普通(約50対戦)'), (100, '長め(約100対戦)'), (1, 'なし(非推奨)'))
    )

    class Meta:
        model = Team
        fields = ('name', 'description', 'page_id', 'one_on_one', 'offset_term')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial = kwargs.get('initial')
        affl = initial.get('affl')
        team = affl.team

        self.fields["name"] = forms.CharField(label="チーム名", max_length=50, required=True, initial=team.name)
        self.fields["description"] = forms.ChoiceField(
            label="チーム説明",
            required=False,
            help_text="チームの説明を入力してください。ランキングを公開する場合、ページの上部に表示されます。",
            initial=team.description
        )
        self.fields["page_id"] = forms.CharField(
            label="キーフレーズ",
            max_length=20,
            required=False,
            help_text="ランキングをシェアする際の文字列を設定します。<br>5文字以上20文字以下の半角英数字で、他のチームですでに使用されている文字列は設定できません。",
            initial=team.page_id
        )
        self.fields["one_on_one"] = forms.ChoiceField(
            label='デフォルト入力方式',
            help_text='対戦結果登録時、初めに表示される入力方式を選択できます',
            choices=((True, '1対1対戦'), (False, '多人数対戦')),
            initial=team.one_on_one
        )
        self.fields['offset_term'] = forms.ChoiceField(
            label='暫定レーティング期間',
            help_text='加入したばかりのプレイヤーには暫定レーティングが設定されます。暫定レーティングを適用する期間を設定してください。<br>この値を変更するとレーティングの再計算が必要になります。',
            choices=((20, '短め(約20対戦)'), (50, '普通(約50対戦)'), (100, '長め(約100対戦)'), (1, 'なし(非推奨)')),
            initial=team.offset_term
        )
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class GameCreateForm(forms.ModelForm):
    name = forms.CharField(
        label='対戦タイトル',
        max_length=50,
        required=False,
        help_text='一覧に表示されますので、わかりやすい名前をつけてみてください'
    )
    date = forms.DateTimeField(
        label='対戦日時',
        required=True,
        initial=make_aware(datetime.datetime.now()),
        help_text='対戦の前後を判断するのに用います。<br>秒は省略できます。時・分・秒をまるまる省略した場合、０時ちょうどとみなされます。'
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
            date = make_aware(parser.parse(input_data['date']))
        except ValueError:
            raise ValidationError('日付の入力形式が間違っています')
        if not self.instance:
            if Game.objects.filter(date=date):
                raise ValidationError('同時に開催されている試合があるようです。時刻をずらしてください。')

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


class GameCreate1on1Form(forms.ModelForm):
    name = forms.CharField(
        label='対戦タイトル',
        max_length=50,
        required=False,
        help_text='一覧に表示されますので、わかりやすい名前をつけてあげてください'
    )
    date = forms.DateTimeField(
        label='対戦日時',
        required=True,
        initial=make_aware(datetime.datetime.now()),
        help_text='試合の前後を判断するのに用います。<br>秒は省略できます。時・分・秒をまるまる省略した場合、０時ちょうどとみなされます。'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial = kwargs.pop('initial')
        player_set = initial.pop('players')
        player_list = []
        for player in player_set:
            player_list += [(player.pk, player.name)]
        players = tuple(player_list)

        self.fields["winner"] = forms.ChoiceField(label="勝者", required=True, choices=players)
        self.fields["loser"] = forms.ChoiceField(label="敗者", required=True, choices=players)
        self.fields["even"] = forms.BooleanField(label="引き分け", required=False, help_text='引き分けの場合チェックをオンにします')

        if 'winner' in initial:
            self.fields['winner'].initial = initial.pop('winner')
            self.fields['loser'].initial = initial.pop('loser')
            self.fields['even'].initial = initial.pop('even')

        for field in self.fields.values():
            if field.label != "引き分け":
                field.widget.attrs['class'] = 'form-control align-middle'
        # self.fields['date'].widget.attrs['id'] = 'datepicker'

    class Meta:
        model = Game
        fields = ('name', 'date')

    def is_valid(self):
        return super().is_valid()

    def clean(self):
        input_data = self.data

        try:
            date = make_aware(parser.parse(input_data['date']))
        except ValueError:
            raise ValidationError('日付の入力形式が間違っています')
        if not self.instance:
            if Game.objects.filter(date=date):
                raise ValidationError('同時に開催されている試合があるようです。時刻をずらしてください。')

        winner = input_data.get("winner")
        loser = input_data.get("loser")
        if winner == loser:
            raise forms.ValidationError("勝者と敗者は異なるプレイヤーとしてください")

        return input_data


class TeamChoiceForm(forms.ModelForm):
    team = forms.ChoiceField(label='チーム')

    class Meta:
        model = Affiliation
        fields = ('team',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        affl = kwargs.get('instance')
        team_set = Team.objects.filter(owner=affl.user)
        team_list = []
        for team in team_set:
            team_list += [(team.pk, team.name)]
        teams = tuple(team_list)

        self.fields["team"] = forms.ChoiceField(label='選択中のチーム', required=True, initial=affl.team, choices=teams)

    def is_valid(self):
        return super().is_valid()

    def clean(self):
        input_data = self.cleaned_data
        team_pk = input_data.get('team')
        input_data['team'] = Team.objects.get(pk=team_pk)
        return input_data


