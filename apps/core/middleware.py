import traceback as tb
from django.conf import settings


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
