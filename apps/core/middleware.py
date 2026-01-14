"""
Middleware de rate limiting pour LysAngels
Protection anti-spam sur les formulaires sensibles
"""
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.shortcuts import render
import hashlib
import time


class RateLimitMiddleware:
    """
    Middleware de rate limiting basé sur IP pour protéger contre le spam
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Configuration du rate limiting par type d'action
        self.limits = {
            'login': {'max_attempts': 5, 'window': 300},  # 5 tentatives en 5 minutes
            'register': {'max_attempts': 3, 'window': 3600},  # 3 inscriptions par heure
            'password_reset': {'max_attempts': 3, 'window': 3600},  # 3 demandes par heure
            'default': {'max_attempts': 30, 'window': 60},  # 30 requêtes par minute
        }

    def __call__(self, request):
        # Vérifier rate limit avant de traiter la requête
        if request.method == 'POST':
            action = self._get_action_type(request.path)
            if action and not self._check_rate_limit(request, action):
                return self._rate_limit_response(request, action)
        
        response = self.get_response(request)
        return response

    def _get_action_type(self, path):
        """Identifier le type d'action basé sur le chemin"""
        if '/login/' in path:
            return 'login'
        elif '/register/' in path:
            return 'register'
        elif '/password-reset/' in path:
            return 'password_reset'
        return None

    def _get_client_ip(self, request):
        """Récupérer l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def _get_cache_key(self, ip, action):
        """Générer une clé de cache unique"""
        hash_input = f"{ip}:{action}"
        return f"ratelimit:{hashlib.md5(hash_input.encode()).hexdigest()}"

    def _check_rate_limit(self, request, action):
        """Vérifier si la limite n'est pas dépassée"""
        ip = self._get_client_ip(request)
        cache_key = self._get_cache_key(ip, action)
        
        limit_config = self.limits.get(action, self.limits['default'])
        max_attempts = limit_config['max_attempts']
        window = limit_config['window']
        
        # Récupérer le compteur actuel
        current = cache.get(cache_key, {'count': 0, 'start_time': time.time()})
        
        # Réinitialiser si la fenêtre est expirée
        if time.time() - current['start_time'] > window:
            current = {'count': 0, 'start_time': time.time()}
        
        # Vérifier la limite
        if current['count'] >= max_attempts:
            return False
        
        # Incrémenter le compteur
        current['count'] += 1
        cache.set(cache_key, current, window)
        
        return True

    def _rate_limit_response(self, request, action):
        """Retourner une réponse d'erreur 429"""
        limit_config = self.limits.get(action, self.limits['default'])
        wait_time = limit_config['window'] // 60  # En minutes
        
        context = {
            'action': action,
            'wait_time': wait_time,
        }
        
        return render(request, 'errors/rate_limit.html', context, status=429)
