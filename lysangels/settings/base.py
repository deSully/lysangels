"""
Common settings shared between dev and production
"""
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'easy_thumbnails',
    # LysAngels apps
    'apps.accounts',
    'apps.vendors',
    'apps.projects',
    'apps.proposals',
    'apps.messaging',
    'apps.core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.vendors.middleware.SubscriptionMiddleware',
]

ROOT_URLCONF = 'lysangels.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'apps.messaging.context_processors.unread_messages_count',
                'apps.core.context_processors.notifications_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'lysangels.wsgi.application'


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Lome'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Login/Logout URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'core:home'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Easy Thumbnails Configuration
THUMBNAIL_ALIASES = {
    '': {
        'small': {'size': (300, 300), 'crop': 'smart', 'quality': 85},
        'medium': {'size': (600, 600), 'crop': 'smart', 'quality': 90},
        'large': {'size': (1200, 900), 'crop': False, 'quality': 90},
        'card': {'size': (400, 400), 'crop': 'smart', 'quality': 85},
        'hero': {'size': (1920, 1080), 'crop': 'smart', 'quality': 90},
    },
}

THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'easy_thumbnails.processors.scale_and_crop',
    'easy_thumbnails.processors.filters',
)

THUMBNAIL_HIGH_RESOLUTION = True
THUMBNAIL_PRESERVE_FORMAT = True
THUMBNAIL_QUALITY = 90

# Cache configuration (default: local memory)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'lysangels-cache',
    }
}
