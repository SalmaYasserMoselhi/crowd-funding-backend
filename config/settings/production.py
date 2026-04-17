from decouple import config
import dj_database_url

from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

SUPABASE_DB_URL = config('SUPABASE_DB_URL', default='')

if SUPABASE_DB_URL:
    DATABASES = {
        'default': dj_database_url.parse(SUPABASE_DB_URL, conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT', default='5432'),
            'OPTIONS': {
                'sslmode': 'require',
            },
        }
    }


# Email (SendGrid via SMTP)
# https://docs.djangoproject.com/en/6.0/topics/email/

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=587)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='apikey')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@crowdfundegypt.com')


# Supabase S3 Storage
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html

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
