"""
Validateurs personnalisés pour les uploads de fichiers
Sécurité renforcée avec vérification MIME type stricte
"""
from django.core.exceptions import ValidationError
import magic
import os


# Tailles maximales (en bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TOTAL_STORAGE_PER_USER = 100 * 1024 * 1024  # 100MB par utilisateur

# MIME types autorisés (whitelist stricte)
ALLOWED_IMAGE_MIMES = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp',
]

ALLOWED_ATTACHMENT_MIMES = [
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/webp',
    'application/pdf',
    'application/msword',  # .doc
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    'application/vnd.ms-excel',  # .xls
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
]

# Extensions autorisées (validation supplémentaire)
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
ALLOWED_ATTACHMENT_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.pdf', '.doc', '.docx', '.xls', '.xlsx']


def validate_file_mime_type(file, allowed_mimes, file_type='fichier'):
    """
    Valide le MIME type réel du fichier (pas juste l'extension)
    Utilise python-magic pour lire les magic bytes
    Retourne le MIME type détecté
    """
    file_mime = None
    try:
        # Lire les premiers bytes pour détecter le vrai type
        file.seek(0)
        file_content = file.read(2048)
        file.seek(0)  # Reset cursor
        
        file_mime = magic.from_buffer(file_content, mime=True)
        
        if file_mime and file_mime not in allowed_mimes:
            raise ValidationError(
                f'Type de {file_type} non autorisé. '
                f'Types acceptés: {", ".join(allowed_mimes)}. '
                f'Type détecté: {file_mime}'
            )
    except (AttributeError, ImportError):
        # Si python-magic n'est pas disponible, fallback sur content_type
        if hasattr(file, 'content_type'):
            file_mime = file.content_type
            if file_mime not in allowed_mimes:
                raise ValidationError(
                    f'Type de {file_type} non autorisé: {file.content_type}. '
                    f'Types acceptés: {", ".join(allowed_mimes)}'
                )
        else:
            # Dernier fallback: validation par extension uniquement
            pass
    
    return file_mime


def validate_file_extension(file, allowed_extensions, file_type='fichier'):
    """Valide l'extension du fichier"""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f'Extension de {file_type} non autorisée: {ext}. '
            f'Extensions acceptées: {", ".join(allowed_extensions)}'
        )


def validate_image_file(image):
    """
    Validation complète d'une image uploadée
    - Taille max 5MB
    - MIME type strict (JPEG, PNG, WebP uniquement)
    - Extension valide
    """
    # 1. Validation de la taille
    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f'La taille de l\'image ne doit pas dépasser 5MB. '
            f'Taille actuelle: {image.size / (1024*1024):.2f}MB'
        )
    
    # 2. Validation de l'extension
    validate_file_extension(image, ALLOWED_IMAGE_EXTENSIONS, 'image')
    
    # 3. Validation du MIME type (sécurité critique)
    validate_file_mime_type(image, ALLOWED_IMAGE_MIMES, 'image')


def validate_attachment_file(attachment):
    """
    Validation complète d'une pièce jointe
    - Taille max 10MB
    - MIME types autorisés (images + PDF + Office)
    - Extension valide
    """
    # 1. Validation de la taille
    if attachment.size > MAX_ATTACHMENT_SIZE:
        raise ValidationError(
            f'La taille de la pièce jointe ne doit pas dépasser 10MB. '
            f'Taille actuelle: {attachment.size / (1024*1024):.2f}MB'
        )
    
    # 2. Validation de l'extension
    validate_file_extension(attachment, ALLOWED_ATTACHMENT_EXTENSIONS, 'pièce jointe')
    
    # 3. Validation du MIME type
    validate_file_mime_type(attachment, ALLOWED_ATTACHMENT_MIMES, 'pièce jointe')


def check_user_storage_quota(user, new_file_size):
    """
    Vérifie si l'utilisateur a atteint sa limite de stockage totale
    Retourne True si OK, lève ValidationError sinon
    """
    # Calculer la taille totale des fichiers de l'utilisateur
    total_size = 0
    
    # Images du vendor profile (si prestataire)
    if hasattr(user, 'vendor_profile'):
        vendor = user.vendor_profile
        
        # Logo
        if vendor.logo:
            try:
                total_size += vendor.logo.size
            except:
                pass
        
        # Images de portfolio
        for image in vendor.images.all():
            try:
                total_size += image.image.size
            except:
                pass
    
    # Pièces jointes dans les messages
    from apps.messaging.models import Message
    messages = Message.objects.filter(sender=user, attachment__isnull=False)
    for msg in messages:
        try:
            if msg.attachment:
                total_size += msg.attachment.size
        except:
            pass
    
    # Vérifier si ajout du nouveau fichier dépasse le quota
    if (total_size + new_file_size) > MAX_TOTAL_STORAGE_PER_USER:
        raise ValidationError(
            f'Quota de stockage dépassé. '
            f'Utilisé: {total_size / (1024*1024):.1f}MB, '
            f'Limite: {MAX_TOTAL_STORAGE_PER_USER / (1024*1024):.0f}MB. '
            f'Veuillez supprimer des fichiers avant d\'en ajouter de nouveaux.'
        )
    
    return True


def get_user_storage_info(user):
    """
    Retourne les informations de stockage de l'utilisateur
    Utile pour afficher dans le dashboard
    """
    total_size = 0
    file_count = 0
    
    if hasattr(user, 'vendor_profile'):
        vendor = user.vendor_profile
        
        if vendor.logo:
            try:
                total_size += vendor.logo.size
                file_count += 1
            except:
                pass
        
        for image in vendor.images.all():
            try:
                total_size += image.image.size
                file_count += 1
            except:
                pass
    
    from apps.messaging.models import Message
    messages = Message.objects.filter(sender=user, attachment__isnull=False)
    for msg in messages:
        try:
            if msg.attachment:
                total_size += msg.attachment.size
                file_count += 1
        except:
            pass
    
    return {
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / (1024*1024), 2),
        'file_count': file_count,
        'quota_bytes': MAX_TOTAL_STORAGE_PER_USER,
        'quota_mb': MAX_TOTAL_STORAGE_PER_USER / (1024*1024),
        'usage_percent': round((total_size / MAX_TOTAL_STORAGE_PER_USER) * 100, 1),
        'remaining_mb': round((MAX_TOTAL_STORAGE_PER_USER - total_size) / (1024*1024), 2),
    }
