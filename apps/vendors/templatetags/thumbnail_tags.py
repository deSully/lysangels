"""
Template tags personnalisés pour les thumbnails et images responsives
"""
from django import template
from easy_thumbnails.files import get_thumbnailer

register = template.Library()


@register.simple_tag
def thumbnail_url(image, alias):
    """
    Génère l'URL d'un thumbnail avec l'alias configuré
    
    Usage: {% thumbnail_url vendor.logo 'small' %}
    """
    if not image:
        return ''
    
    try:
        thumbnailer = get_thumbnailer(image)
        thumbnail = thumbnailer.get_thumbnail({'alias': alias})
        return thumbnail.url
    except Exception:
        return image.url if hasattr(image, 'url') else ''


@register.simple_tag
def responsive_srcset(image, *aliases):
    """
    Génère un attribut srcset pour images responsives
    
    Usage: {% responsive_srcset vendor.logo 'small' 'medium' 'large' %}
    Retourne: "small.jpg 300w, medium.jpg 600w, large.jpg 1200w"
    """
    if not image:
        return ''
    
    srcset_parts = []
    
    # Mapping des alias vers leurs tailles en largeur
    size_mapping = {
        'small': '300w',
        'medium': '600w',
        'large': '1200w',
        'card': '400w',
        'hero': '1920w',
    }
    
    try:
        thumbnailer = get_thumbnailer(image)
        
        for alias in aliases:
            thumbnail = thumbnailer.get_thumbnail({'alias': alias})
            width = size_mapping.get(alias, '1x')
            srcset_parts.append(f"{thumbnail.url} {width}")
        
        return ', '.join(srcset_parts)
    except Exception:
        # Fallback vers l'image originale
        return image.url if hasattr(image, 'url') else ''


