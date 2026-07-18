"""
Utilitaires de cache pour les données de référence
Les types de services et événements changent rarement, on peut les mettre en cache
"""
from django.core.cache import cache
from apps.vendors.models import ServiceType
from apps.projects.models import EventType


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


def get_cached_event_types():
    """
    Récupère les types d'événements depuis le cache (durée: 1 heure)
    Si pas en cache, requête DB et mise en cache
    """
    event_types = cache.get('event_types')

    if event_types is None:
        event_types = list(EventType.objects.all().order_by('name'))
        cache.set('event_types', event_types, 3600)

    return event_types


def clear_reference_cache():
    cache.delete_many(['service_types_ordered', 'service_types', 'event_types'])
