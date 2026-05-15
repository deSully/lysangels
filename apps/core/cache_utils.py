"""
Utilitaires de cache pour les données de référence
Les types de services et événements changent rarement, on peut les mettre en cache
"""
from django.core.cache import cache
from apps.vendors.models import ServiceType


def get_cached_service_types(ordered=True):
    """
    Récupère les types de services depuis le cache (durée: 1 heure)
    Si pas en cache, requête DB et mise en cache
    """
    cache_key = 'service_types_ordered' if ordered else 'service_types'
    service_types = cache.get(cache_key)
    
    if service_types is None:
        if ordered:
            service_types = list(ServiceType.objects.all().order_by('name'))
        else:
            service_types = list(ServiceType.objects.all())
        
        # Cache pour 1 heure (3600 secondes)
        cache.set(cache_key, service_types, 3600)
    
    return service_types


def clear_reference_cache():
    cache.delete_many(['service_types_ordered', 'service_types'])
