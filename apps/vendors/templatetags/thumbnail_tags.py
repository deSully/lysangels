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


@register.simple_tag
def thumbnail_with_fallback(image, alias, fallback_text=''):
    """
    Génère l'URL du thumbnail avec fallback vers image originale
    
    Usage: {% thumbnail_with_fallback vendor.logo 'medium' %}
    """
    if not image:
        return ''
    
    try:
        thumbnailer = get_thumbnailer(image)
        thumbnail = thumbnailer.get_thumbnail({'alias': alias})
        return thumbnail.url
    except Exception:
        # Fallback vers l'image originale si thumbnail échoue
        return image.url if hasattr(image, 'url') else ''


@register.inclusion_tag('vendors/components/responsive_image.html')
def responsive_image(image, alt='', css_class='', sizes='100vw', lazy=True):
    """
    Inclusion tag pour générer une image responsive complète
    
    Usage: {% responsive_image vendor.logo "Logo" "w-full h-full" %}
    """
    if not image:
        return {
            'has_image': False,
            'alt': alt,
            'css_class': css_class,
        }
    
    try:
        thumbnailer = get_thumbnailer(image)
        
        # Générer les thumbnails
        small = thumbnailer.get_thumbnail({'alias': 'small'})
        medium = thumbnailer.get_thumbnail({'alias': 'medium'})
        large = thumbnailer.get_thumbnail({'alias': 'large'})
        
        # Construire le srcset
        srcset = f"{small.url} 300w, {medium.url} 600w, {large.url} 1200w"
        
        return {
            'has_image': True,
            'src': medium.url,  # Image par défaut (600px)
            'srcset': srcset,
            'sizes': sizes,
            'alt': alt,
            'css_class': css_class,
            'lazy': lazy,
        }
    except Exception:
        # Fallback vers l'image originale
        return {
            'has_image': True,
            'src': image.url,
            'srcset': '',
            'sizes': sizes,
            'alt': alt,
            'css_class': css_class,
            'lazy': lazy,
        }
