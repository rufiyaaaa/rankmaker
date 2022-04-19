from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """拡張ユーザーモデル"""
    have_team = models.BooleanField(verbose_name='紐づいているチームの有無', blank=True)

    class Meta:
        verbose_name_plural = 'CustomUser'
