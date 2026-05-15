from django.conf import settings


def analytics(request):
    return {
        'UMAMI_WEBSITE_ID': getattr(settings, 'UMAMI_WEBSITE_ID', ''),
    }
