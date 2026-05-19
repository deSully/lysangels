from django.utils import timezone

EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'

_model = None


class EmbedError(Exception):
    pass


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as e:
            raise EmbedError(f'Impossible de charger le modèle d\'embedding : {e}') from e
    return _model


def build_vendor_text(vendor):
    parts = [vendor.business_name]
    if vendor.description:
        parts.append(vendor.description)
    service_names = [s.name for s in vendor.service_types.all()]
    if service_names:
        parts.append(', '.join(service_names))
    return ' | '.join(parts)


def embed_text(text):
    """Génère un vecteur d'embedding pour un texte. Retourne une liste de floats.
    Lève EmbedError si le modèle ne peut pas être chargé ou si l'encodage échoue.
    """
    try:
        model = _get_model()
        return model.encode(text).tolist()
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
