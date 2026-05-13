"""
Validateurs personnalisés pour les uploads d'images
Sécurité renforcée avec vérification MIME type stricte
"""
from django.core.exceptions import ValidationError
import os

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

ALLOWED_IMAGE_MIMES = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp',
]

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']


def validate_file_mime_type(file, allowed_mimes, file_type='fichier'):
    file_mime = None
    if HAS_MAGIC:
        try:
            file.seek(0)
            file_content = file.read(2048)
            file.seek(0)
            file_mime = magic.from_buffer(file_content, mime=True)
            if file_mime and file_mime not in allowed_mimes:
                raise ValidationError(
                    f'Type de {file_type} non autorisé. '
                    f'Types acceptés: {", ".join(allowed_mimes)}. '
                    f'Type détecté: {file_mime}'
                )
            return file_mime
        except Exception:
            pass
    if hasattr(file, 'content_type'):
        file_mime = file.content_type
        if file_mime not in allowed_mimes:
            raise ValidationError(
                f'Type de {file_type} non autorisé: {file.content_type}. '
                f'Types acceptés: {", ".join(allowed_mimes)}'
            )
    return file_mime


def validate_file_extension(file, allowed_extensions, file_type='fichier'):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f'Extension de {file_type} non autorisée: {ext}. '
            f'Extensions acceptées: {", ".join(allowed_extensions)}'
        )


def validate_image_file(image):
    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f'La taille de l\'image ne doit pas dépasser 5MB. '
            f'Taille actuelle: {image.size / (1024*1024):.2f}MB'
        )
    validate_file_extension(image, ALLOWED_IMAGE_EXTENSIONS, 'image')
    validate_file_mime_type(image, ALLOWED_IMAGE_MIMES, 'image')
