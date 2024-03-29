from .settings_common import *

# 本番運用環境用にセキュリティキーを生成し環境変数から読み込む
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# デバッグモードを有効にするかどうか（本番運用では必ずFalseにする）
DEBUG = False

# django_SESをINSTALLED＿APPSに追加
INSTALLED_APPS += [
    "django_ses",
]

# 許可するホスト名のリスト
Hostlist = os.environ.get('ALLOWED_HOSTS').split(",")
ALLOWED_HOSTS = Hostlist

# 静的ファイルを配置する場所
STATIC_ROOT = '/usr/share/nginx/html/static'
MEDIA_ROOT = '/usr/share/nginx/html/media'

# Amazon SES関連設定
AWS_SES_ACCESS_KEY_ID = os.environ.get('AWS_SES_ACCESS_KEY_ID')
AWS_SES_SECRET_ACCESS_KEY = os.environ.get('AWS_SES_SECRET_ACCESS_KEY')
ses_backend = 'django_ses.SESBackend'
EMAIL_BACKEND = ses_backend

# ロギング
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    # ロガーの設定
    'loggers': {
        # Djangoが利用するロガー
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        # multiアプリケーションが利用するロガー
        'multi': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        # accountsアプリケーションが利用するロガー
        'accounts': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },

    # ハンドラの設定
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django.log'),
            'formatter': 'prod',
            'when': 'D',  # ログローテーション（新しいファイルへの切り替え）間隔の単位（D=日）
            'interval': 1,  # ログローテーション間隔（1日単位）
            'backupCount': 7,  # 保存しておくログファイル数
        },
    },

    # フォーマッタの設定
    'formatters': {
        'prod': {
            'format': '\t'.join([
                '%(asctime)s',
                '[%(levelname)s]',
                '%(pathname)s(lineno)d)',
                '%(message)s'
            ])
        },
    }
}

# ドメイン登録後にCSRFエラーが出るようになったので追加
CSRF_TRUSTED_ORIGINS = ['rankmaker.jp']
