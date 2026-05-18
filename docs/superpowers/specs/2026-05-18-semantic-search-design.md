# Recherche Sémantique LysAngels — Design Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer la recherche textuelle (`icontains`) par une recherche sémantique vectorielle : taper "gateaux" retourne les prestataires Pâtisserie, "sono" retourne Sono & Éclairage, etc.

**Architecture:** Embeddings générés via API Groq (`nomic-embed-text-v1.5`, 768 dimensions) stockés en JSONField sur `VendorProfile`. Recherche par similarité cosinus calculée en Python. Fallback `icontains` si Groq indisponible.

**Tech Stack:** Django 6, Python 3.12, Groq API (embeddings), SQLite (dev), PostgreSQL/Neon (prod), `requests` (déjà installé)

---

## Comportement attendu

### Page prestataires sans recherche
Comportement inchangé : prestataires groupés par catégorie.

### Page prestataires avec recherche
- "gateaux" → liste plate des prestataires Pâtisserie (et Traiteur si pertinent), triés par score
- "photo" → Photographe + Photobooth & Divertissement
- "mariage africain" → tous prestataires sémantiquement proches
- Titre : `X résultats pour « gateaux »`
- Aucun résultat pertinent (score < 0.30) → message "Aucun résultat" + suggestion de parcourir les catégories
- Si Groq indisponible → fallback silencieux `icontains` (le site ne casse pas)

---

## Modèle de données

### Champs ajoutés à `VendorProfile`

```python
embedding = models.JSONField(null=True, blank=True)
# Liste de 768 floats. Null = pas encore vectorisé.

embedding_updated_at = models.DateTimeField(null=True, blank=True)
# Timestamp de la dernière vectorisation.
```

**Migration :** `0010_vendorprofile_embedding.py`

### Texte vectorisé par profil

```python
def build_vendor_text(vendor):
    parts = [vendor.business_name]
    if vendor.description:
        parts.append(vendor.description)
    service_names = [s.name for s in vendor.service_types.all()]
    if service_names:
        parts.append(', '.join(service_names))
    return ' | '.join(parts)

# Exemple : "Chez Aminata Pâtisserie | Spécialiste gâteaux de mariage | Pâtisserie, Décoration"
```

---

## Nouveaux fichiers

### `apps/vendors/embedding.py`

Responsabilités :
- `build_vendor_text(vendor) -> str` — construit le texte à vectoriser
- `embed_text(text: str) -> list[float] | None` — appel Groq API, retourne None si erreur ou clé absente
- `vectorize_vendor(vendor_id: int) -> bool` — vectorise un profil, retourne True si succès
- `vectorize_pending_vendors() -> int` — vectorise tous les profils sans embedding, retourne le nombre traité

**Appel Groq :**
```python
import requests
from django.conf import settings

GROQ_API_URL = "https://api.groq.com/openai/v1/embeddings"
GROQ_MODEL = "nomic-embed-text-v1.5"

def embed_text(text: str):
    api_key = getattr(settings, 'GROQ_API_KEY', None)
    if not api_key:
        return None
    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": GROQ_MODEL, "input": text},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
    except Exception:
        return None
```

### `apps/vendors/search.py`

Responsabilités :
- `cosine_similarity(a, b) -> float` — produit scalaire normalisé entre deux vecteurs Python
- `semantic_search(query: str, limit: int = 20) -> list[VendorProfile]` — embed la requête, calcule la similarité avec tous les profils vectorisés actifs, trie par score, filtre score < 0.30, retourne les `limit` meilleurs
- Si `embed_text` retourne None → fallback `icontains` sur `business_name` + `description`

```python
def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def semantic_search(query, limit=20):
    query_vec = embed_text(query)
    if query_vec is None:
        # fallback texte
        return list(
            VendorProfile.objects.filter(is_active=True).filter(
                Q(business_name__icontains=query) | Q(description__icontains=query)
            ).prefetch_related('service_types', 'images', 'cities')[:limit]
        )
    candidates = VendorProfile.objects.filter(
        is_active=True, embedding__isnull=False
    ).prefetch_related('service_types', 'images', 'cities')
    scored = []
    for vendor in candidates:
        score = cosine_similarity(query_vec, vendor.embedding)
        if score >= 0.30:
            scored.append((score, vendor))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [v for _, v in scored[:limit]]
```

### `apps/vendors/management/commands/vectorize_vendors.py`

Commande : `python manage.py vectorize_vendors`
- Vectorise tous les profils sans embedding
- Affiche la progression : "3/12 — Chez Aminata... OK"
- Option `--all` pour re-vectoriser même ceux déjà vectorisés

---

## Fichiers modifiés

### `apps/vendors/views.py` — `vendor_list`

```python
from .search import semantic_search

def vendor_list(request):
    search = request.GET.get('search', '').strip()
    ...
    if search:
        results = semantic_search(search, limit=20)
        context = {
            'search_results': results,
            'search_query': search,
            'is_search': True,
            ...
        }
        return render(request, 'vendors/vendor_list.html', context)
    # sinon : comportement catégories inchangé
    ...
```

### `templates/vendors/vendor_list.html`

Nouveau bloc conditionnel :
```html
{% if is_search %}
  <h2>{{ search_results|length }} résultat{% if search_results|length != 1 %}s{% endif %} pour « {{ search_query }} »</h2>
  {% if search_results %}
    <div class="vendors-grid">
      {% for vendor in search_results %}
        <!-- carte prestataire identique aux cartes catégories -->
      {% endfor %}
    </div>
  {% else %}
    <p>Aucun prestataire trouvé. <a href="{% url 'vendors:vendor_list' %}">Parcourir les catégories</a></p>
  {% endif %}
{% else %}
  <!-- vue catégories actuelle -->
{% endif %}
```

### `apps/accounts/admin_views.py`

Deux nouvelles vues protégées par `@admin_required` :

**`vectorize_all_vendors_view(request)`** — POST uniquement
- Appelle `vectorize_pending_vendors()`
- Redirige vers la liste admin avec message flash : "N profils vectorisés"

**`vectorize_single_vendor_view(request, pk)`** — POST uniquement
- Appelle `vectorize_vendor(pk)`
- Redirige vers la fiche admin du prestataire avec message flash

### `apps/accounts/urls.py`

```python
path('admin/vendors/vectorize-all/', views.vectorize_all_vendors_view, name='admin_vendor_vectorize_all'),
path('admin/vendors/<int:pk>/vectorize/', views.vectorize_single_vendor_view, name='admin_vendor_vectorize'),
```

### `templates/accounts/admin/vendor_list.html`

Bouton en haut de la liste (dans le header ou toolbar) :
```html
<form method="post" action="{% url 'accounts:admin_vendor_vectorize_all' %}">
  {% csrf_token %}
  <button type="submit" class="btn-secondary">
    ↺ Vectoriser les profils manquants ({{ non_vectorized_count }} / {{ total_vendors_count }})
  </button>
</form>
```
Le contexte de la vue `vendor_list` admin doit inclure `non_vectorized_count` et `total_vendors_count`.

### `templates/accounts/admin/vendor_detail.html`

Badge + bouton dans la section infos du prestataire :
```html
{% if vendor.embedding %}
  <span class="badge-green">● Vectorisé — {{ vendor.embedding_updated_at|timesince }}</span>
  <form method="post" action="{% url 'accounts:admin_vendor_vectorize' vendor.pk %}">
    {% csrf_token %}
    <button type="submit" class="btn-sm-secondary">↺ Re-vectoriser</button>
  </form>
{% else %}
  <span class="badge-red">● Non vectorisé</span>
  <form method="post" action="{% url 'accounts:admin_vendor_vectorize' vendor.pk %}">
    {% csrf_token %}
    <button type="submit" class="btn-sm-primary">Vectoriser ce profil</button>
  </form>
{% endif %}
```

---

## Configuration

### Variables d'environnement

```
GROQ_API_KEY=gsk_xxxxx   # Absent = search sémantique désactivée, fallback icontains
```

### `lysangels/settings/base.py`

```python
GROQ_API_KEY = env('GROQ_API_KEY', default='')
```

---

## Contraintes et règles

- **Pas de tests unitaires** (convention du projet)
- **Pas de framework JS** — les boutons admin sont des `<form method="post">` classiques
- **Synchrone** — la vectorisation est bloquante (admin seulement, ~1 seconde acceptable)
- **Pas d'auto-inscription prestataire** — la vectorisation n'est déclenchée que par l'admin
- **Compatibilité migrations** — migration additive uniquement (nullable fields)
- **Aucun `Co-Authored-By` en commit**
- **Demander validation avant chaque commit**

---

## Ordre d'implémentation recommandé

1. Migration + champs `embedding` / `embedding_updated_at` sur `VendorProfile`
2. `apps/vendors/embedding.py` (embed_text, build_vendor_text, vectorize_vendor, vectorize_pending_vendors)
3. `apps/vendors/search.py` (cosine_similarity, semantic_search avec fallback)
4. Mise à jour `vendor_list` view + template (bloc résultats de recherche)
5. Commande management `vectorize_vendors`
6. Vues admin (vectorize_all, vectorize_single) + routes
7. Templates admin (bouton liste + badge/bouton fiche)
