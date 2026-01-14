#!/usr/bin/env python3
"""
Génère les icônes PWA pour LysAngels
Nécessite: pip install pillow
"""

import os
from PIL import Image, ImageDraw, ImageFont

# Configuration
ICON_SIZES = [32, 96, 144, 192, 512]
OUTPUT_DIR = 'static/images/icons'
ICON_COLOR = '#8B5CF6'  # lily-purple
BG_COLOR = '#FFFFFF'  # blanc

def create_icon(size, output_path):
    """Crée une icône carrée avec le logo LysAngels"""
    # Créer une image avec fond blanc
    img = Image.new('RGB', (size, size), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Dessiner un cercle violet
    margin = size // 8
    circle_bbox = [margin, margin, size - margin, size - margin]
    draw.ellipse(circle_bbox, fill=ICON_COLOR)
    
    # Dessiner un lys stylisé (3 pétales)
    center_x, center_y = size // 2, size // 2
    petal_height = size // 3
    petal_width = size // 6
    
    # Couleur blanche pour le lys
    lily_color = '#FFFFFF'
    
    # Pétale central (haut)
    draw.polygon([
        (center_x, center_y - petal_height // 2),
        (center_x - petal_width // 3, center_y + petal_height // 4),
        (center_x + petal_width // 3, center_y + petal_height // 4)
    ], fill=lily_color)
    
    # Pétale gauche
    draw.polygon([
        (center_x - petal_width, center_y - petal_height // 4),
        (center_x - petal_width // 4, center_y + petal_height // 4),
        (center_x, center_y)
    ], fill=lily_color)
    
    # Pétale droit
    draw.polygon([
        (center_x + petal_width, center_y - petal_height // 4),
        (center_x + petal_width // 4, center_y + petal_height // 4),
        (center_x, center_y)
    ], fill=lily_color)
    
    # Sauvegarder
    img.save(output_path, 'PNG', quality=95, optimize=True)
    print(f"✅ Icône créée: {output_path} ({size}x{size})")

def main():
    """Génère toutes les icônes"""
    # Créer le dossier si nécessaire
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("🎨 Génération des icônes PWA pour LysAngels...")
    print(f"📁 Dossier de sortie: {OUTPUT_DIR}")
    print()
    
    # Générer chaque taille
    for size in ICON_SIZES:
        output_path = os.path.join(OUTPUT_DIR, f'icon-{size}x{size}.png')
        create_icon(size, output_path)
    
    print()
    print("✨ Toutes les icônes ont été générées avec succès!")
    print()
    print("📋 Fichiers créés:")
    for size in ICON_SIZES:
        print(f"   - icon-{size}x{size}.png")

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("❌ Erreur: Pillow n'est pas installé")
        print("   Installez-le avec: pip install pillow")
    except Exception as e:
        print(f"❌ Erreur: {e}")
