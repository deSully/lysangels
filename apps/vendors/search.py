from django.db.models import Q
from .models import VendorProfile, ServiceType


def semantic_search(query, limit=20):
    """Recherche par mots-clés sur les types de service.

    Trouve les ServiceType dont le nom ou les search_keywords contiennent la requête,
    puis retourne les prestataires actifs qui ont ces services.
    Fallback sur le nom et la description des prestataires si aucun service ne correspond.
    """
    q = query.strip()
    if not q:
        return []

    matching_services = ServiceType.objects.filter(
        Q(name__icontains=q) | Q(search_keywords__icontains=q)
    )

    if matching_services.exists():
        return list(
            VendorProfile.objects.filter(
                is_active=True,
                service_types__in=matching_services,
            ).distinct().prefetch_related('service_types', 'images', 'cities')[:limit]
        )

    return list(
        VendorProfile.objects.filter(is_active=True).filter(
            Q(business_name__icontains=q) | Q(description__icontains=q)
        ).prefetch_related('service_types', 'images', 'cities')[:limit]
    )
