import requests
from django.conf import settings
from django.utils import timezone


GROQ_API_URL = "https://api.groq.com/openai/v1/embeddings"
GROQ_MODEL = "nomic-embed-text-v1.5"


class EmbedError(Exception):
    pass


def build_vendor_text(vendor):
    """Construit le texte à vectoriser pour un profil prestataire."""
    parts = [vendor.business_name]
    if vendor.description:
        parts.append(vendor.description)
    service_names = [s.name for s in vendor.service_types.all()]
    if service_names:
        parts.append(', '.join(service_names))
    return ' | '.join(parts)


def embed_text(text):
    """Appelle l'API Groq pour obtenir un vecteur d'embedding.
    Retourne une liste de 768 floats.
    Lève EmbedError avec un message explicite en cas de problème.
    """
    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        raise EmbedError('GROQ_API_KEY non configurée dans les settings')
    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": GROQ_MODEL, "input": text},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
    except requests.exceptions.HTTPError as e:
        raise EmbedError(f'HTTP {e.response.status_code} — {e.response.text[:300]}') from e
    except requests.exceptions.Timeout:
        raise EmbedError('Timeout Groq API (> 10s)') from None
    except EmbedError:
        raise
    except Exception as e:
        raise EmbedError(str(e)) from e


def vectorize_vendor(vendor_id):
    """Génère et sauvegarde l'embedding pour un profil donné.
    Retourne (True, None) si succès, (False, message_erreur) sinon.
    """
    from .models import VendorProfile
    try:
        vendor = VendorProfile.objects.prefetch_related('service_types').get(pk=vendor_id)
    except VendorProfile.DoesNotExist:
        return False, 'Profil introuvable'
    text = build_vendor_text(vendor)
    try:
        vec = embed_text(text)
    except EmbedError as e:
        return False, str(e)
    vendor.embedding = vec
    vendor.embedding_updated_at = timezone.now()
    vendor.save(update_fields=['embedding', 'embedding_updated_at'])
    return True, None


def vectorize_pending_vendors():
    """Vectorise tous les profils dont l'embedding est null.
    Retourne le nombre de profils vectorisés avec succès.
    """
    from .models import VendorProfile
    pks = list(VendorProfile.objects.filter(embedding__isnull=True).values_list('pk', flat=True))
    count = 0
    for pk in pks:
        success, _ = vectorize_vendor(pk)
        if success:
            count += 1
    return count
