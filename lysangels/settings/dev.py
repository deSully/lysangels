"""
Development settings - for local development only
Uses SQLite, DEBUG=True, console email backend
"""
from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$c(r!$v2+2=5hpa&@_xsc5wh-rl@q-4+a44_mhiy)&8im_s&-6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Site URL for emails and notifications
SITE_URL = 'http://localhost:8000'


# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Email - Console backend (prints to terminal)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'LysAngels <noreply@lysangels.tg>'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
