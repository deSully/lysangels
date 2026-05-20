import traceback as tb
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


_RATE_LIMITS = {
    '/accounts/login/':                              (5,  5 * 60),
    '/projects/creer/':                              (10, 60 * 60),
    '/contact/':                                     (20, 60 * 60),
    '/vendors/devenir-prestataire/candidature/':     (10, 60 * 60),
}


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST':
            rule = _RATE_LIMITS.get(request.path)
            if rule:
                limit, window = rule
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR', '')
                key = f'rl:{request.path}:{ip}'
                count = cache.get(key, 0)
                if count >= limit:
                    return HttpResponse('Trop de tentatives. Veuillez réessayer plus tard.', status=429)
                cache.set(key, count + 1, timeout=window)
        return self.get_response(request)


class ErrorLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if settings.DEBUG:
            return None
        try:
            from .models import ErrorLog
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
            ErrorLog.objects.create(
                url=request.path[:500],
                method=request.method,
                error_type=type(exception).__name__,
                error_message=str(exception)[:1000],
                traceback=tb.format_exc(),
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )
        except Exception:
            pass
        return None
