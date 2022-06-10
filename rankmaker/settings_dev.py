from .settings_common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)#!_k&_1kqfad*5(5%!nqy=6@r$h+pncyr4s_&&cgh8(yk_y!1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# ロギング設定
LOGGING = {
    'version': 1,  # 1固定
    'disable_existing_loggers': False,

    # ロガーの設定
    'loggers': {
        # Djangoが利用するロガー
        'Django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        # Diaryアプリケーションが利用するロガー
        'duel': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },

    # ハンドラの設定
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'dev'
        },
    },

    # フォーマッタの設定
    'formatters': {
        'dev': {
            'format': '\t'.join([
                '%(asctime)s'
                '[%(levelname)s]',
                '%(pathname)s(Line:%(lineno)d)',
                '%(message)s%'
            ])
        },
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# list 11.1
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
