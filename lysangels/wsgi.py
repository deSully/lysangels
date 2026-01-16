"""
WSGI config for lysangels project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Use prod settings by default in production (Railway sets DJANGO_SETTINGS_MODULE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lysangels.settings.prod')

application = get_wsgi_application()
