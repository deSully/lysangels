from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def optimize_image_to_webp(image_file, quality=85, max_width=1920, max_height=1080):
    """
    Optimise une image en la convertissant en WebP avec compression
    
    Args:
        image_file: Fichier image uploadé (InMemoryUploadedFile ou UploadedFile)
        quality: Qualité de compression WebP (1-100, défaut 85)
        max_width: Largeur maximale en pixels (défaut 1920)
        max_height: Hauteur maximale en pixels (défaut 1080)
    
    Returns:
        InMemoryUploadedFile: Fichier image optimisé en WebP
    
    Usage:
        # Dans une vue
        if request.FILES.get('image'):
            original_image = request.FILES['image']
            optimized_image = optimize_image_to_webp(original_image)
            profile.image = optimized_image
            profile.save()
    """
    # Ouvrir l'image avec Pillow
    img = Image.open(image_file)
    
    # Convertir en RGB si nécessaire (WebP ne supporte pas RGBA avec qualité optimale)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Créer un fond blanc pour les images transparentes
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Redimensionner si l'image dépasse les dimensions max
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    
    # Sauvegarder en WebP dans un buffer
    output = BytesIO()
    img.save(output, format='WEBP', quality=quality, method=6)
    output.seek(0)
    
    # Générer le nouveau nom de fichier
    original_name = image_file.name.rsplit('.', 1)[0]
    new_name = f"{original_name}.webp"
    
    # Créer un nouveau InMemoryUploadedFile
    optimized_file = InMemoryUploadedFile(
        output,
        'ImageField',
        new_name,
        'image/webp',
        sys.getsizeof(output),
        None
    )
    
    return optimized_file


def create_thumbnail(image_file, size=(300, 300), quality=80):
    """
    Crée une miniature de l'image
    
    Args:
        image_file: Fichier image uploadé
        size: Tuple (largeur, hauteur) de la miniature
        quality: Qualité WebP (défaut 80)
    
    Returns:
        InMemoryUploadedFile: Miniature en WebP
    
    Usage:
        # Créer une version miniature pour les listes
        thumbnail = create_thumbnail(original_image, size=(200, 200))
        profile.thumbnail = thumbnail
    """
    img = Image.open(image_file)
    
    # Convertir en RGB si nécessaire
    if img.mode != 'RGB':
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        else:
            img = img.convert('RGB')
    
    # Créer la miniature (crop centré)
    img.thumbnail(size, Image.Resampling.LANCZOS)
    
    # Sauvegarder en WebP
    output = BytesIO()
    img.save(output, format='WEBP', quality=quality)
    output.seek(0)
    
    # Nom de fichier
    original_name = image_file.name.rsplit('.', 1)[0]
    new_name = f"{original_name}_thumb.webp"
    
    thumbnail_file = InMemoryUploadedFile(
        output,
        'ImageField',
        new_name,
        'image/webp',
        sys.getsizeof(output),
        None
    )
    
    return thumbnail_file


def get_image_dimensions(image_file):
    """
    Récupère les dimensions d'une image sans la charger complètement
    
    Args:
        image_file: Fichier image
    
    Returns:
        tuple: (largeur, hauteur) en pixels
    """
    img = Image.open(image_file)
    return img.size


def compress_image_preserve_format(image_file, quality=85):
    """
    Compresse une image en préservant son format original
    Utile si vous ne voulez pas tout convertir en WebP
    
    Args:
        image_file: Fichier image uploadé
        quality: Qualité de compression (1-100)
    
    Returns:
        InMemoryUploadedFile: Image compressée
    """
    img = Image.open(image_file)
    
    # Déterminer le format original
    original_format = img.format or 'JPEG'
    
    # Convertir en RGB si JPEG
    if original_format == 'JPEG' and img.mode != 'RGB':
        img = img.convert('RGB')
    
    output = BytesIO()
    
    # Paramètres de sauvegarde selon le format
    save_params = {'quality': quality, 'optimize': True}
    
    if original_format == 'PNG':
        save_params = {'optimize': True, 'compress_level': 9}
    
    img.save(output, format=original_format, **save_params)
    output.seek(0)
    
    # Extension appropriée
    ext_map = {'JPEG': '.jpg', 'PNG': '.png', 'GIF': '.gif', 'WEBP': '.webp'}
    ext = ext_map.get(original_format, '.jpg')
    
    original_name = image_file.name.rsplit('.', 1)[0]
    new_name = f"{original_name}{ext}"
    
    compressed_file = InMemoryUploadedFile(
        output,
        'ImageField',
        new_name,
        f'image/{original_format.lower()}',
        sys.getsizeof(output),
        None
    )
    
    return compressed_file
