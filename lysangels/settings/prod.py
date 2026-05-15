"""
Production settings - for deployment
Uses PostgreSQL, environment variables, strict security
"""
from .base import *
import dj_database_url
import os

# ==============================================================================
# SECURITY
# ==============================================================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-dev-key-change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = ["lysangels.com", "www.lysangels.com", "alpha.lysangels.com"]

# Site URL
SITE_URL = os.environ.get('SITE_URL', 'https://lysangels.tg')


# ==============================================================================
# DATABASE
# ==============================================================================
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Fallback to SQLite if no DATABASE_URL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================
# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# X-Frame-Options
X_FRAME_OPTIONS = 'DENY'

# Secure browser XSS filter
SECURE_BROWSER_XSS_FILTER = True

# Content type sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# Referrer policy
SECURE_REFERRER_POLICY = 'same-origin'


# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================
EMAIL_BACKEND_TYPE = os.environ.get('EMAIL_BACKEND', 'console')

if EMAIL_BACKEND_TYPE == 'smtp':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'LysAngels <noreply@lysangels.tg>')
else:
    # Fallback to console for testing
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'LysAngels <noreply@lysangels.tg>'

SERVER_EMAIL = DEFAULT_FROM_EMAIL


# ==============================================================================
# STATIC & MEDIA FILES
# ==============================================================================
# WhiteNoise for serving static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Static files - collect with: python manage.py collectstatic
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# CLOUDINARY (Media files storage)
# ==============================================================================

MEDIA_URL = '/media/'


# ==============================================================================
# LOGGING
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


# 1. Indique à Django qu'il est derrière un proxy (Railway) qui gère le HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 2. Désactive la redirection SSL forcée par Django (car Railway s'en occupe déjà)
SECURE_SSL_REDIRECT = False

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True