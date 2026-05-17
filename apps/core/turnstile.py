import requests
from django.conf import settings

TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


def verify_turnstile(token: str) -> bool:
    """Vérifie un token Cloudflare Turnstile côté serveur. Fail-closed : retourne False en cas d'erreur réseau."""
    if not token:
        return False
    try:
        resp = requests.post(TURNSTILE_VERIFY_URL, data={
            'secret': settings.TURNSTILE_SECRET,
            'response': token,
        }, timeout=5)
        return resp.json().get('success', False)
    except Exception:
        return False
