"""
Development settings - for local development only
Uses SQLite, DEBUG=True, Resend SMTP email
"""
import os
from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$c(r!$v2+2=5hpa&@_xsc5wh-rl@q-4+a44_mhiy)&8im_s&-6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Site URL for emails and notifications
SITE_URL = 'http://localhost:8000'


# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Email — Resend via SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'resend'
EMAIL_HOST_PASSWORD = os.environ.get('RESEND_API_KEY', '')
DEFAULT_FROM_EMAIL = 'LysAngels <susy@lysangels.com>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
