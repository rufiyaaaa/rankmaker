import logging
import os

from django import forms
from django.core.mail import EmailMessage

from .models import Match, Player, Affiliation, Team
from django.core.exceptions import ValidationError


class InquiryForm(forms.Form):
    name = forms.CharField(label='お名前', max_length=30)
    email = forms.EmailField(label='メールアドレス')
    title = forms.CharField(label='タイトル', max_length=30)
    message = forms.CharField(label='メッセージ', widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['name'].widget.attrs['placeholder'] = 'ここに名前を入力'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['placeholder'] = 'ここにメールアドレスを入力'
        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['title'].widget.attrs['placeholder'] = 'ここにタイトルを入力'
        self.fields['message'].widget.attrs['class'] = 'form-control'
        self.fields['message'].widget.attrs['placeholder'] = 'ここにメッセージを入力'

    def send_email(self):
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        title = self.cleaned_data['title']
        message = self.cleaned_data['message']

        subject = 'お問い合わせ {}'.format(title)
        message = '送信者 {0}\nメールアドレス: {1}\nメッセージ:\n{2}'.format(name, email, message)
        from_email = os.environ.get('FROM_EMAIL')
        to_list = [
            os.environ.get('FROM_EMAIL')
        ]
        cc_list = [
            email
        ]

        message = EmailMessage(subject=subject, body=message, from_email=from_email, to=to_list, cc=cc_list)
        message.send()


class CustomModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj): # label_from_instance 関数をオーバーライド
        return obj.name


class MatchCreateForm(forms.ModelForm):
    winner = forms.ModelChoiceField(
        queryset=Player.objects.all(),
        label='勝者',
        empty_label='選択してください',
        to_field_name='name',
    )
    loser = forms.ModelChoiceField(
        queryset=Player.objects.all(),
        label='敗者',
        empty_label='選択してください',
        to_field_name='name',
    )
    even = forms.BooleanField(
        label='引き分け',
        initial=None,
        required=False,
    )

    class Meta:
        model = Match
        fields = ('winner', 'loser', 'even', 'date',)

    def __init__(self, *args, **kwargs):
        match = kwargs['instance']
        if match:
            kwargs['initial'] = {'winner': match.winner, 'loser': match.loser}
        userteam = kwargs.pop('team')
        self.base_fields["winner"].queryset = Player.objects.filter(team=userteam)
        self.base_fields["loser"].queryset = Player.objects.filter(team=userteam)
        super().__init__(*args, **kwargs)
        # for field in self.fields.values():
            # if field.name != 'even':
                # field.widget.attrs['class'] = 'form-control'

    def clean(self):
        winner = self.cleaned_data['winner']
        loser = self.cleaned_data['loser']
        if winner == loser:
            raise ValidationError('勝者と敗者は異なる人物にしてください')


class PlayerCreateForm(forms.ModelForm):
    name = forms.CharField(label='名前', max_length=30)

    class Meta:
        model = Player
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class TeamCreateForm(forms.ModelForm):
    name = forms.CharField(label='チーム名', max_length=30)

    class Meta:
        model = Team
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class TeamConfigForm(forms.ModelForm):
    name = forms.CharField(label='チーム名', max_length=30)

    class Meta:
        model = Team
        fields = ('name',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

