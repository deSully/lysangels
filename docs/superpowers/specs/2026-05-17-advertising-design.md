# Système publicitaire LysAngels — Design

## Objectif

Permettre à l'admin LysAngels de configurer des bannières publicitaires sur 4 zones du site. Plusieurs annonceurs peuvent occuper la même zone ; leurs pubs tournent automatiquement côté client (crossfade toutes les 15 secondes) sans rechargement de page.

## Architecture

Nouvelle app Django `apps/ads`, isolée. Ne modifie aucun modèle existant. Un context processor injecte les pubs actives dans les vues concernées.

**Tech stack :** Django 6 / Python 3.12, SQLite (dev) / PostgreSQL (prod), JS vanilla (pas de lib externe), Whitenoise pour les images uploadées.

---

## Modèle de données

### `Advertisement`

| Champ | Type | Contraintes |
|---|---|---|
| `zone` | `CharField(max_length=30, choices=ZONE_CHOICES)` | Obligatoire |
| `image` | `ImageField(upload_to='ads/')` | Obligatoire |
| `link_url` | `URLField(blank=True)` | Optionnel — si vide, bannière non cliquable |
| `alt_text` | `CharField(max_length=200)` | Obligatoire (accessibilité) |
| `start_date` | `DateField()` | Obligatoire |
| `end_date` | `DateField()` | Obligatoire |
| `is_active` | `BooleanField(default=True)` | Désactivation manuelle |
| `created_at` | `DateTimeField(auto_now_add=True)` | Auto |

**ZONE_CHOICES :**
```python
HERO = 'hero'                          # Bannière pleine largeur homepage (1200×300px)
BETWEEN_SECTIONS = 'between_sections'  # Bande inter-sections homepage (1200×120px)
VENDOR_LIST_TOP = 'vendor_list_top'    # Top page liste prestataires (900×200px)
VENDOR_DETAIL = 'vendor_detail'        # Bas fiche prestataire (900×200px)
```

**Méthode utilitaire :**
```python
@classmethod
def active_for_zone(cls, zone):
    today = date.today()
    return cls.objects.filter(
        zone=zone,
        is_active=True,
        start_date__lte=today,
        end_date__gte=today,
    )
```

---

## Context processor

`apps/ads/context_processors.py` — injecte dans chaque requête un dict `ads` avec les pubs actives par zone :

```python
def ads(request):
    return {
        'ads': {
            'hero': Advertisement.active_for_zone('hero'),
            'between_sections': Advertisement.active_for_zone('between_sections'),
            'vendor_list_top': Advertisement.active_for_zone('vendor_list_top'),
            'vendor_detail': Advertisement.active_for_zone('vendor_detail'),
        }
    }
```

Ajouté dans `TEMPLATES[0]['OPTIONS']['context_processors']` dans `base.py`.

---

## Rotation côté client

Chaque zone dans le template rend toutes ses pubs empilées (la première visible, les autres `display:none`). Un script JS global (~15 lignes) détecte les groupes `.ad-rotator` et fait un crossfade toutes les 15 secondes :

```html
{% if ads.hero %}
<div class="ad-rotator ad-zone-hero">
  {% for ad in ads.hero %}
  <div class="ad-slide" {% if not forloop.first %}style="display:none"{% endif %}>
    {% if ad.link_url %}
    <a href="{{ ad.link_url }}" target="_blank" rel="noopener sponsored">
      <img src="{{ ad.image.url }}" alt="{{ ad.alt_text }}">
    </a>
    {% else %}
    <img src="{{ ad.image.url }}" alt="{{ ad.alt_text }}">
    {% endif %}
  </div>
  {% endfor %}
</div>
{% endif %}
```

Le script JS est inclus dans `base.html` (conditionnel : uniquement si le context processor a injecté des pubs).

---

## Pages modifiées

| Template | Zone | Position |
|---|---|---|
| `templates/core/home.html` | `hero` | Après `.hero-bar` (stats), avant la section services |
| `templates/core/home.html` | `between_sections` | Entre section `featured-bg` et section `steps-bg` |
| `templates/vendors/vendor_list.html` | `vendor_list_top` | Avant la grille de résultats |
| `templates/vendors/vendor_detail.html` | `vendor_detail` | Avant le footer, après le contenu principal |

Chaque bloc est strictement conditionnel (`{% if ads.hero %}`). Si aucune pub active → rien ne s'affiche, la page est identique à aujourd'hui.

---

## Dashboard admin

Nouvelle section **"Publicités"** dans le menu du dashboard admin existant (`apps/accounts/admin_views.py`).

**Vues ajoutées :**
- `ads_list` — liste toutes les pubs, groupées par zone, avec statut (actif / expiré / inactif)
- `ad_create` — formulaire création
- `ad_edit` — formulaire édition
- `ad_delete` — suppression avec confirmation

**URL prefix :** `/accounts/admin/ads/`

**Statut calculé (affiché dans la liste) :**
- `Actif` — is_active=True + dates valides aujourd'hui
- `Planifié` — is_active=True + start_date dans le futur
- `Expiré` — end_date dépassée
- `Inactif` — is_active=False

---

## Règles métier

- Une pub expirée (end_date < today) n'est jamais affichée, même si is_active=True
- Une pub désactivée (is_active=False) n'est jamais affichée, même si les dates sont valides
- Si une zone n'a aucune pub active, le bloc HTML correspondant n'est pas rendu
- link_url est optionnel — bannière non cliquable si vide
- Les images sont servies par Whitenoise en prod (upload_to='ads/' → MEDIA_ROOT/ads/)

---

## Fichiers créés / modifiés

**Créés :**
- `apps/ads/__init__.py`
- `apps/ads/models.py`
- `apps/ads/context_processors.py`
- `apps/ads/admin_views.py`
- `apps/ads/urls.py`
- `apps/ads/migrations/0001_initial.py`
- `templates/ads/ad_list.html`
- `templates/ads/ad_form.html`

**Modifiés :**
- `lysangels/settings/base.py` — INSTALLED_APPS + context_processors + MEDIA_ROOT/MEDIA_URL
- `lysangels/urls.py` — inclusion urls ads admin + serving MEDIA en dev
- `apps/accounts/admin_views.py` — lien menu "Publicités"
- `templates/accounts/admin/base_admin.html` — entrée nav "Publicités"
- `templates/core/home.html` — zones A et B
- `templates/vendors/vendor_list.html` — zone C
- `templates/vendors/vendor_detail.html` — zone D
- `templates/base.html` — script JS rotation
