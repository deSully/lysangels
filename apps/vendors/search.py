from django.db.models import Q
from .embedding import embed_query, EmbedError
from .models import VendorProfile


def cosine_similarity(a, b):
    """Similarité cosinus entre deux vecteurs Python (listes de floats)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_search(query, limit=20):
    """Recherche sémantique parmi les profils actifs.

    Si Groq est disponible : embed la requête, calcule la similarité cosinus
    avec tous les profils vectorisés, retourne les `limit` plus pertinents
    (score >= 0.30).

    Si Groq indisponible (clé absente ou erreur) : fallback icontains sur
    business_name et description.

    Retourne une liste de VendorProfile (pas un QuerySet).
    """
    try:
        query_vec = embed_query(query)
    except EmbedError:
        query_vec = None

    if query_vec is None:
        return list(
            VendorProfile.objects.filter(is_active=True).filter(
                Q(business_name__icontains=query) | Q(description__icontains=query)
            ).prefetch_related('service_types', 'images', 'cities')[:limit]
        )

    candidates = list(
        VendorProfile.objects.filter(
            is_active=True, embedding__isnull=False
        ).prefetch_related('service_types', 'images', 'cities')
    )

    scored = []
    for vendor in candidates:
        score = cosine_similarity(query_vec, vendor.embedding)
        if score >= 0.50:
            scored.append((score, vendor))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [v for _, v in scored[:limit]]
