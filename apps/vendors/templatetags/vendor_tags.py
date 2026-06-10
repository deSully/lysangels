from django import template
import re

register = template.Library()


@register.filter(name='google_maps_embed')
def google_maps_embed(url):
    """
    Convertit un lien Google Maps en URL embed

    Formats supportés:
    - https://maps.app.goo.gl/xxxxx
    - https://goo.gl/maps/xxxxx
    - https://www.google.com/maps/place/...
    - https://www.google.com/maps/@latitude,longitude,...
    """
    if not url:
        return ''

    # Si c'est déjà une URL embed, la retourner telle quelle
    if 'google.com/maps/embed' in url:
        return url

    # Essayer d'extraire les coordonnées si présentes dans l'URL
    # Format: @latitude,longitude
    coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if coord_match:
        lat, lng = coord_match.groups()
        return f'https://www.google.com/maps/embed/v1/view?key=&center={lat},{lng}&zoom=15'

    # Pour les liens raccourcis ou les liens place, utiliser l'URL directement dans l'embed
    # Note: L'embed peut ne pas fonctionner parfaitement sans API key Google Maps
    # Alternative: retourner l'URL originale pour ouverture directe
    return url


@register.filter(name='is_google_maps_embeddable')
def is_google_maps_embeddable(url):
    """
    Vérifie si l'URL Google Maps peut être intégrée
    """
    if not url:
        return False

    # Vérifier si l'URL contient des coordonnées
    if re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url):
        return True

    # Vérifier si c'est déjà une URL embed
    if 'google.com/maps/embed' in url:
        return True

    return False


@register.filter(name='instagram_url')
def instagram_url(value):
    """
    Normalise un handle/URL Instagram en URL complète.
    Accepte : 'moncompte', '@moncompte', 'https://instagram.com/moncompte', etc.
    Retourne : 'https://instagram.com/moncompte'
    """
    if not value:
        return ''
    value = value.strip()
    # Si c'est déjà une URL complète, extraire le handle
    match = re.search(r'instagram\.com/([^/?#\s]+)', value)
    if match:
        handle = match.group(1).lstrip('@')
        return f'https://instagram.com/{handle}'
    # Sinon, nettoyer le @ et construire l'URL
    handle = value.lstrip('@')
    return f'https://instagram.com/{handle}'
