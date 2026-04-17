from decouple import config
import dj_database_url

from .base import *  # noqa: F401, F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASE_URL = config('SUPABASE_DB_URL', default=config('DATABASE_URL', default=''))
if not DATABASE_URL:
    raise ValueError('Set SUPABASE_DB_URL (or DATABASE_URL) in your environment.')

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Email
# https://docs.djangoproject.com/en/6.0/topics/email/

EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@crowdfundegypt.com')


# Storage
USE_S3 = config('USE_S3', cast=bool, default=False)

if not USE_S3:
    USE_S3 = bool(
        config('AWS_ACCESS_KEY_ID', default=config('SUPABASE_S3_ACCESS_KEY', default=''))
        and config('AWS_SECRET_ACCESS_KEY', default=config('SUPABASE_S3_SECRET_KEY', default=''))
        and config('AWS_STORAGE_BUCKET_NAME', default=config('SUPABASE_S3_BUCKET_NAME', default=''))
    )

if USE_S3:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default=config('SUPABASE_S3_ACCESS_KEY', default=''))
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default=config('SUPABASE_S3_SECRET_KEY', default=''))
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default=config('SUPABASE_S3_BUCKET_NAME', default=''))
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default=config('SUPABASE_S3_REGION', default='us-east-1'))
    AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default='')
    AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL', default=config('SUPABASE_S3_ENDPOINT_URL', default='')) or None
    AWS_S3_ADDRESSING_STYLE = config('AWS_S3_ADDRESSING_STYLE', default='virtual')
    AWS_S3_SIGNATURE_VERSION = config('AWS_S3_SIGNATURE_VERSION', default='s3v4')
    AWS_QUERYSTRING_EXPIRE = config('AWS_QUERYSTRING_EXPIRE', cast=int, default=3600)

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not AWS_STORAGE_BUCKET_NAME:
        raise ValueError(
            'S3 is enabled but credentials are incomplete. Set AWS_* vars or SUPABASE_S3_* vars.'
        )

    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = config('AWS_QUERYSTRING_AUTH', cast=bool, default=True)
    AWS_DEFAULT_ACL = None
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    else:
        MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/'

    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
else:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Max upload size: 5MB (enforced at Django level)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
