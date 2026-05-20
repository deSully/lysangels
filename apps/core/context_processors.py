from django.conf import settings


def analytics(request):
    return {
        'UMAMI_WEBSITE_ID': getattr(settings, 'UMAMI_WEBSITE_ID', ''),
    }


def unresolved_errors(request):
    if not request.path.startswith('/accounts/admin'):
        return {}
    try:
        from .models import ErrorLog
        return {'unresolved_errors_count': ErrorLog.objects.filter(is_resolved=False).count()}
    except Exception:
        return {}


def global_stats(request):
    try:
        from apps.vendors.models import VendorProfile
        count = VendorProfile.objects.filter(is_active=True).count()
    except Exception:
        count = 0
    return {'vendor_count': count}
