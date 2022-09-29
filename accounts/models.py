from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """拡張ユーザーモデル"""
    have_multi_team = models.BooleanField(verbose_name='紐づいているmultiチームの有無', blank=True, default=False)
    confirm_privacy_policy = models.BooleanField(verbose_name='プライバシーポリシーへの同意', blank=True, default=False)

    class Meta:
        verbose_name_plural = 'CustomUser'
