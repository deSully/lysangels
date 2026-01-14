# Structure des Images - LysAngels

## Organisation des Dossiers

```
static/images/
├── heroes/                  # Images principales pour bannières et cartes événements
│   ├── mariage-africain.jpg
│   ├── corporate-africain.jpg
│   └── celebration-africaine.jpg
├── events/                  # Images par catégorie d'événements
│   ├── mariages/
│   ├── corporate/
│   └── celebrations/
├── icons/                   # Icônes de l'application (PWA)
│   ├── icon-192x192.png
│   ├── icon-512x512.png
│   └── ...
└── og-image.jpg            # Image par défaut pour partages réseaux sociaux
```

## Spécifications des Images

### Images Heroes (bannières principales)
- **Emplacement**: `heroes/`
- **Dimensions recommandées**: 1920x1080px minimum
- **Format**: JPEG optimisé (ou WebP + fallback JPEG)
- **Poids maximum**: 200-300KB après optimisation
- **Ratio**: 16:9
- **Usage**: Cartes d'événements sur la page d'accueil

### Images Events (galerie)
- **Emplacement**: `events/[categorie]/`
- **Dimensions recommandées**: 1200x800px
- **Format**: JPEG optimisé
- **Poids maximum**: 150-200KB
- **Usage**: Galeries de prestataires, exemples de réalisations

### Icons (PWA)
- **Emplacement**: `icons/`
- **Dimensions**: 32x32, 96x96, 128x128, 192x192, 512x512
- **Format**: PNG transparent
- **Usage**: Application web progressive, favicons

### OG Image (réseaux sociaux)
- **Emplacement**: racine (`og-image.jpg`)
- **Dimensions**: 1200x630px
- **Format**: JPEG
- **Poids maximum**: 200KB
- **Usage**: Aperçu lors du partage sur Facebook, Twitter, etc.

## Nommage des Fichiers

### Convention
- Utiliser des noms descriptifs en français
- Séparer les mots par des tirets (kebab-case)
- Indiquer la catégorie si pertinent
- Exemples:
  - `mariage-traditionnel-togo.jpg`
  - `conference-entreprise-lome.jpg`
  - `anniversaire-enfant-africain.jpg`

### À Éviter
- ❌ Espaces dans les noms de fichiers
- ❌ Caractères spéciaux (accents, etc.)
- ❌ Noms génériques (image1.jpg, photo.jpg)

## Optimisation des Images

### Outils Recommandés
1. **TinyPNG** (https://tinypng.com) - Compression intelligente
2. **Squoosh** (https://squoosh.app) - Outil Google, conversion WebP
3. **ImageOptim** (Mac) - Application native
4. **GIMP** - Édition et export optimisé

### Commande ImageMagick (si installé)
```bash
# Redimensionner et optimiser
convert input.jpg -resize 1920x1080^ -gravity center -extent 1920x1080 -quality 85 output.jpg

# Convertir en WebP
cwebp -q 80 input.jpg -o output.webp
```

### Script Python d'Optimisation
```python
from PIL import Image

def optimize_image(input_path, output_path, max_size=(1920, 1080), quality=85):
    img = Image.open(input_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    img.save(output_path, "JPEG", quality=quality, optimize=True)

# Usage
optimize_image("source.jpg", "heroes/mariage-africain.jpg")
```

## Checklist avant Upload

- [ ] Image représente la culture africaine/togolaise
- [ ] Droits d'utilisation vérifiés (licence CC0 ou équivalente)
- [ ] Dimensions appropriées (1920x1080 minimum pour heroes)
- [ ] Image optimisée (poids < 300KB)
- [ ] Nom de fichier descriptif et sans espaces
- [ ] Qualité visuelle professionnelle (nette, bien exposée)
- [ ] Testé sur différents devices (desktop, mobile)

## Licences et Crédits

### Images Actuelles
Toutes les images doivent être:
- Libres de droits (CC0, Public Domain)
- Sous licence commerciale appropriée
- Créditées si requis par la licence

### Documentation des Sources
Maintenir un fichier `CREDITS.md` listant:
- Nom de l'image
- Source (photographe, site)
- Licence
- Date d'ajout

Exemple:
```markdown
## mariage-africain.jpg
- Source: Unsplash / Photographe: John Doe
- Licence: CC0 (domaine public)
- URL: https://unsplash.com/photos/xxxxx
- Ajouté le: 2026-01-14
```

## Maintenance

### Révision Périodique
- Revoir les images tous les 6 mois
- Remplacer les images obsolètes ou de mauvaise qualité
- Ajouter de nouvelles images pour diversifier
- Vérifier que les liens/sources sont toujours valides

### Sauvegarde
- Conserver les images originales (non optimisées) séparément
- Backup régulier du dossier `static/images/`
- Version control (Git LFS pour grandes images si nécessaire)

## Support

Pour toute question sur la gestion des images, contactez l'équipe technique LysAngels.
