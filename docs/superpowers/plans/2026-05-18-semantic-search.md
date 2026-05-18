# Recherche Sémantique — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer la recherche textuelle `icontains` par une recherche vectorielle sémantique via embeddings Groq — "gateaux" retourne les prestataires Pâtisserie, "sono" retourne Sono & Éclairage, etc.

**Architecture:** Chaque profil `VendorProfile` stocke un vecteur (768 floats, JSONField). L'API Groq (`nomic-embed-text-v1.5`) génère les embeddings. La recherche calcule la similarité cosinus en Python pur. Fallback `icontains` si Groq indisponible.

**Tech Stack:** Django 6, Python 3.12, Groq API (embeddings gratuits), `requests` (déjà installé), SQLite (dev), PostgreSQL/Neon (prod)

**Contraintes projet :**
- Pas de tests unitaires
- Pas de `Co-Authored-By` dans les commits
- Demander validation avant chaque `git commit` — montrer le diff + message proposé, attendre approbation explicite
- Pas de push sur origin

---

## Structure des fichiers

| Fichier | Action | Rôle |
|---------|--------|------|
| `lysangels/settings/base.py` | Modifier | Ajouter `GROQ_API_KEY` |
| `.env.example` | Modifier | Documenter la nouvelle variable |
| `apps/vendors/models.py` | Modifier | Ajouter `embedding` + `embedding_updated_at` |
| `apps/vendors/migrations/0010_vendorprofile_embedding.py` | Créer (via makemigrations) | Migration additive |
| `apps/vendors/embedding.py` | Créer | `build_vendor_text`, `embed_text`, `vectorize_vendor`, `vectorize_pending_vendors` |
| `apps/vendors/search.py` | Créer | `cosine_similarity`, `semantic_search` avec fallback |
| `apps/vendors/views.py` | Modifier | Branche `if search:` → `semantic_search()` |
| `templates/vendors/vendor_list.html` | Modifier | Bloc résultats de recherche (liste plate) |
| `apps/vendors/management/__init__.py` | Créer | Package Python |
| `apps/vendors/management/commands/__init__.py` | Créer | Package Python |
| `apps/vendors/management/commands/vectorize_vendors.py` | Créer | Commande CLI batch |
| `apps/accounts/admin_views.py` | Modifier | 2 nouvelles vues vectorisation |
| `apps/accounts/urls.py` | Modifier | 2 nouvelles routes |
| `templates/accounts/admin/vendor_list.html` | Modifier | Bouton "Vectoriser les profils manquants" |
| `templates/accounts/admin/vendor_detail.html` | Modifier | Badge statut + bouton vectoriser |

---

## Task 1 : Configurer GROQ_API_KEY

**Files:**
- Modify: `lysangels/settings/base.py`
- Modify: `.env.example`

- [ ] **Étape 1 : Ajouter GROQ_API_KEY dans base.py**

Ouvrir `lysangels/settings/base.py`. Trouver les lignes TURNSTILE (ligne ~137) et ajouter juste après :

```python
GROQ_API_KEY = config('GROQ_API_KEY', default='')
```

Le fichier utilise `from decouple import config` (déjà présent ligne 5). La valeur `default=''` signifie que le site fonctionne sans cette clé — la recherche retombe sur `icontains`.

- [ ] **Étape 2 : Documenter dans .env.example**

Ajouter à la fin de `.env.example` :

```
# Groq API (recherche sémantique)
# Générer une clé sur https://console.groq.com/keys
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- [ ] **Étape 3 : Vérifier que le serveur démarre**

```bash
python manage.py check
```

Résultat attendu : `System check identified no issues (0 silenced).`

- [ ] **Étape 4 : Montrer le diff et proposer le commit — attendre approbation**

```bash
rtk git diff lysangels/settings/base.py .env.example
```

Message de commit proposé : `feat: ajoute GROQ_API_KEY pour la recherche sémantique`

---

## Task 2 : Migration — champs embedding sur VendorProfile

**Files:**
- Modify: `apps/vendors/models.py`
- Create: `apps/vendors/migrations/0010_vendorprofile_embedding.py` (via makemigrations)

- [ ] **Étape 1 : Ajouter les champs au modèle**

Dans `apps/vendors/models.py`, trouver la classe `VendorProfile` et ajouter les deux champs après le champ `is_featured` (ou tout autre endroit logique avant `created_at`) :

```python
embedding = models.JSONField(
    null=True, blank=True,
    help_text='Vecteur d\'embedding (768 floats). Null = pas encore vectorisé.'
)
embedding_updated_at = models.DateTimeField(
    null=True, blank=True,
    verbose_name='Vectorisé le'
)
```

- [ ] **Étape 2 : Générer la migration**

```bash
python manage.py makemigrations vendors --name vendorprofile_embedding
```

Résultat attendu : `Migrations for 'vendors': apps/vendors/migrations/0010_vendorprofile_embedding.py`

- [ ] **Étape 3 : Vérifier le contenu de la migration**

Le fichier `apps/vendors/migrations/0010_vendorprofile_embedding.py` doit contenir deux `AddField` pour `embedding` et `embedding_updated_at`, tous deux `null=True`. Il ne doit PAS contenir de `AlterField` ou `RemoveField` sur des champs existants.

- [ ] **Étape 4 : Appliquer la migration**

```bash
python manage.py migrate
```

Résultat attendu : `Applying vendors.0010_vendorprofile_embedding... OK`

- [ ] **Étape 5 : Vérifier en shell**

```bash
python manage.py shell -c "
from apps.vendors.models import VendorProfile
v = VendorProfile.objects.first()
print(v.embedding, v.embedding_updated_at)
"
```

Résultat attendu : `None None`

- [ ] **Étape 6 : Montrer le diff et proposer le commit — attendre approbation**

```bash
rtk git diff apps/vendors/models.py
```

Message de commit proposé : `feat: ajoute champs embedding sur VendorProfile (migration 0010)`

---

## Task 3 : Créer apps/vendors/embedding.py

**Files:**
- Create: `apps/vendors/embedding.py`

- [ ] **Étape 1 : Créer le fichier**

Créer `apps/vendors/embedding.py` avec le contenu suivant :

```python
import requests
from django.conf import settings
from django.utils import timezone


GROQ_API_URL = "https://api.groq.com/openai/v1/embeddings"
GROQ_MODEL = "nomic-embed-text-v1.5"


def build_vendor_text(vendor):
    """Construit le texte à vectoriser pour un profil prestataire."""
    parts = [vendor.business_name]
    if vendor.description:
        parts.append(vendor.description)
    service_names = [s.name for s in vendor.service_types.all()]
    if service_names:
        parts.append(', '.join(service_names))
    return ' | '.join(parts)


def embed_text(text):
    """Appelle l'API Groq pour obtenir un vecteur d'embedding.
    Retourne une liste de 768 floats, ou None si la clé est absente / erreur réseau.
    """
    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        return None
    try:
        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": GROQ_MODEL, "input": text},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]
    except Exception:
        return None


def vectorize_vendor(vendor_id):
    """Génère et sauvegarde l'embedding pour un profil donné.
    Retourne True si succès, False si erreur (clé absente, API down, profil inexistant).
    """
    from .models import VendorProfile
    try:
        vendor = VendorProfile.objects.prefetch_related('service_types').get(pk=vendor_id)
    except VendorProfile.DoesNotExist:
        return False
    text = build_vendor_text(vendor)
    vec = embed_text(text)
    if vec is None:
        return False
    vendor.embedding = vec
    vendor.embedding_updated_at = timezone.now()
    vendor.save(update_fields=['embedding', 'embedding_updated_at'])
    return True


def vectorize_pending_vendors():
    """Vectorise tous les profils dont l'embedding est null.
    Retourne le nombre de profils vectorisés avec succès.
    """
    from .models import VendorProfile
    pks = list(VendorProfile.objects.filter(embedding__isnull=True).values_list('pk', flat=True))
    count = 0
    for pk in pks:
        if vectorize_vendor(pk):
            count += 1
    return count
```

- [ ] **Étape 2 : Vérifier l'import depuis le shell**

```bash
python manage.py shell -c "
from apps.vendors.embedding import build_vendor_text
from apps.vendors.models import VendorProfile
v = VendorProfile.objects.prefetch_related('service_types').first()
if v:
    print(build_vendor_text(v))
else:
    print('Aucun profil en base')
"
```

Résultat attendu : une chaîne comme `Chez Aminata | Spécialiste gâteaux... | Pâtisserie`  
Si la DB est vide en dev, créer un profil via `python manage.py load_demo_vendors` avant de vérifier.

- [ ] **Étape 3 : Vérifier embed_text sans clé**

```bash
python manage.py shell -c "
from apps.vendors.embedding import embed_text
result = embed_text('test')
print('Sans clé:', result)
"
```

Résultat attendu : `Sans clé: None` (la clé GROQ_API_KEY n'est pas encore dans .env dev)

- [ ] **Étape 4 : Montrer le diff et proposer le commit — attendre approbation**

```bash
rtk git diff apps/vendors/embedding.py
```

Message de commit proposé : `feat: module embedding.py — appel Groq API + vectorisation prestataires`

---

## Task 4 : Créer apps/vendors/search.py

**Files:**
- Create: `apps/vendors/search.py`

- [ ] **Étape 1 : Créer le fichier**

Créer `apps/vendors/search.py` avec le contenu suivant :

```python
from django.db.models import Q
from .embedding import embed_text
from .models import VendorProfile


def cosine_similarity(a, b):
    """Similarité cosinus entre deux vecteurs Python (listes de floats)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def semantic_search(query, limit=20):
    """Recherche sémantique parmi les profils actifs.

    Si Groq est disponible : embed la requête, calcule la similarité cosinus
    avec tous les profils vectorisés, retourne les `limit` plus pertinents
    (score >= 0.30).

    Si Groq indisponible (clé absente ou erreur) : fallback icontains sur
    business_name et description.

    Retourne une liste de VendorProfile (pas un QuerySet).
    """
    query_vec = embed_text(query)

    if query_vec is None:
        return list(
            VendorProfile.objects.filter(is_active=True).filter(
                Q(business_name__icontains=query) | Q(description__icontains=query)
            ).prefetch_related('service_types', 'images', 'cities')[:limit]
        )

    candidates = list(
        VendorProfile.objects.filter(
            is_active=True, embedding__isnull=False
        ).prefetch_related('service_types', 'images', 'cities')
    )

    scored = []
    for vendor in candidates:
        score = cosine_similarity(query_vec, vendor.embedding)
        if score >= 0.30:
            scored.append((score, vendor))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [v for _, v in scored[:limit]]
```

- [ ] **Étape 2 : Vérifier l'import depuis le shell**

```bash
python manage.py shell -c "
from apps.vendors.search import semantic_search, cosine_similarity
# Test cosinus sur vecteurs triviaux
a = [1.0, 0.0]
b = [1.0, 0.0]
print('cosine([1,0],[1,0]):', cosine_similarity(a, b))  # doit afficher 1.0
c = [0.0, 1.0]
print('cosine([1,0],[0,1]):', cosine_similarity(a, c))  # doit afficher 0.0
print('Import OK')
"
```

Résultat attendu :
```
cosine([1,0],[1,0]): 1.0
cosine([1,0],[0,1]): 0.0
Import OK
```

- [ ] **Étape 3 : Vérifier le fallback sans clé**

```bash
python manage.py shell -c "
from apps.vendors.search import semantic_search
results = semantic_search('photo')
print(f'{len(results)} résultats (fallback icontains)')
for r in results[:3]:
    print(' -', r.business_name)
"
```

Résultat attendu : liste des prestataires dont le nom/description contient "photo" (ou liste vide si base vide).

- [ ] **Étape 4 : Montrer le diff et proposer le commit — attendre approbation**

Message de commit proposé : `feat: module search.py — recherche cosinus + fallback icontains`

---

## Task 5 : Mettre à jour vendor_list view + template

**Files:**
- Modify: `apps/vendors/views.py`
- Modify: `templates/vendors/vendor_list.html`

- [ ] **Étape 1 : Mettre à jour vendor_list dans views.py**

Remplacer la fonction `vendor_list` dans `apps/vendors/views.py` par :

```python
def vendor_list(request):
    """Liste publique des prestataires — catégories ou résultats de recherche"""
    from .search import semantic_search

    service_type_ids = request.GET.getlist('service_types')
    search = request.GET.get('search', '').strip()
    country_id = request.GET.get('country_id', '').strip()
    city_id = request.GET.get('city_id', '').strip()

    all_service_types = get_cached_service_types(ordered=True)

    base_context = {
        'service_types': all_service_types,
        'selected_service_types': service_type_ids,
        'search_query': search,
        'total_vendors': VendorProfile.objects.filter(is_active=True).count(),
        'countries': Country.objects.filter(is_active=True).order_by('display_order', 'name'),
        'cities_json': _build_cities_json(),
        'selected_country_id': country_id,
        'selected_city_id': city_id,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Prestataires'},
        ],
    }

    if search:
        results = semantic_search(search, limit=20)
        return render(request, 'vendors/vendor_list.html', {
            **base_context,
            'search_results': results,
            'is_search': True,
        })

    if service_type_ids:
        active_service_types = [s for s in all_service_types if str(s.id) in service_type_ids]
    else:
        active_service_types = all_service_types

    vendors_by_category = []
    for service_type in active_service_types:
        qs = VendorProfile.objects.filter(is_active=True, service_types=service_type)
        if city_id:
            qs = qs.filter(cities__id=city_id)
        elif country_id:
            qs = qs.filter(cities__country_id=country_id)
        qs = qs.prefetch_related(
            'cities', 'service_types', 'images'
        ).order_by('-is_featured', '-created_at').distinct()[:6]
        if qs.exists():
            vendors_by_category.append({'service_type': service_type, 'vendors': qs})

    return render(request, 'vendors/vendor_list.html', {
        **base_context,
        'vendors_by_category': vendors_by_category,
        'is_search': False,
    })
```

Note : l'import `from .search import semantic_search` est en import local à l'intérieur de la fonction pour éviter une dépendance circulaire potentielle lors des migrations.

- [ ] **Étape 2 : Ajouter le bloc résultats dans vendor_list.html**

Dans `templates/vendors/vendor_list.html`, trouver la ligne avec `<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">` (environ ligne 325).

Juste après cette ligne, insérer le bloc suivant **avant** le bloc `{% if vendors_by_category %}` existant :

```html
        {% if is_search %}
        <!-- ── RÉSULTATS DE RECHERCHE ── -->
        <div class="mb-6">
            <h2 style="font-size:1.1rem; font-weight:700; color:var(--night); letter-spacing:-.01em;">
                {% if search_results %}
                    {{ search_results|length }} résultat{% if search_results|length != 1 %}s{% endif %} pour <em style="font-style:normal; color:var(--terra);">« {{ search_query }} »</em>
                {% else %}
                    Aucun résultat pour <em style="font-style:normal; color:var(--terra);">« {{ search_query }} »</em>
                {% endif %}
            </h2>
        </div>
        {% if search_results %}
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4 mb-14">
            {% for vendor in search_results %}
            <a href="{% url 'vendors:vendor_detail' vendor.id %}" class="vcard">
                {% if vendor.logo %}
                    <img src="{{ vendor.logo.url }}" alt="{{ vendor.business_name }}" loading="lazy" decoding="async">
                {% elif vendor.images.first %}
                    <img src="{% thumbnail_url vendor.images.first.image 'medium' %}"
                         alt="{{ vendor.business_name }}" loading="lazy" decoding="async">
                {% else %}
                    <div class="vcard-placeholder">
                        <span class="vcard-letter font-display">{{ vendor.business_name|first|upper }}</span>
                    </div>
                {% endif %}
                <div class="vcard-veil"></div>
                <div class="vcard-arrow" aria-hidden="true">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
                    </svg>
                </div>
                <div class="vcard-body">
                    <div class="vcard-tags">
                        {% for service in vendor.service_types.all|slice:":2" %}
                        <span class="vcard-tag">{{ service.name|truncatewords:2 }}</span>
                        {% endfor %}
                    </div>
                    <div class="vcard-name font-display">{{ vendor.business_name }}</div>
                    {% with vendor.cities.first as city %}
                    {% if city %}
                    <div class="vcard-city">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                        </svg>
                        {{ city.name }}
                    </div>
                    {% endif %}
                    {% endwith %}
                </div>
            </a>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty-wrap">
            <div class="empty-inner">
                <div class="empty-icon">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                </div>
                <h3 class="empty-title font-display">Aucun résultat</h3>
                <p class="empty-sub">Aucun prestataire ne correspond à votre recherche. Parcourez les catégories pour trouver ce dont vous avez besoin.</p>
                <a href="{% url 'vendors:vendor_list' %}" class="empty-cta-primary">
                    Voir tous les prestataires
                </a>
            </div>
        </div>
        {% endif %}
        {% else %}
```

Ensuite, trouver la balise fermante `{% endif %}` qui ferme le bloc `{% if vendors_by_category %}` (tout à la fin du contenu principal) et ajouter `{% endif %}` juste après pour fermer le `{% else %}` du bloc recherche.

La structure finale de `<main>` sera :
```
<main ...>
  {% if is_search %}
    ... résultats ...
  {% else %}
    {% if vendors_by_category %}
      ... catégories ...
    {% else %}
      ... empty state ...
    {% endif %}
  {% endif %}
</main>
```

- [ ] **Étape 3 : Vérifier manuellement**

```bash
python manage.py runserver
```

Ouvrir `http://localhost:8000/prestataires/` :
1. Sans recherche → les catégories s'affichent normalement ✓
2. Taper "photo" dans le champ → page se recharge, affiche "X résultats pour « photo »" avec une grille de cartes (fallback icontains car pas de clé Groq en dev) ✓
3. Effacer la recherche (clic ×) → retour aux catégories ✓

- [ ] **Étape 4 : Montrer le diff et proposer le commit — attendre approbation**

```bash
rtk git diff apps/vendors/views.py templates/vendors/vendor_list.html
```

Message de commit proposé : `feat: recherche sémantique — vue liste + template résultats`

---

## Task 6 : Commande management vectorize_vendors

**Files:**
- Create: `apps/vendors/management/__init__.py`
- Create: `apps/vendors/management/commands/__init__.py`
- Create: `apps/vendors/management/commands/vectorize_vendors.py`

- [ ] **Étape 1 : Créer les __init__.py**

```bash
mkdir -p apps/vendors/management/commands
touch apps/vendors/management/__init__.py
touch apps/vendors/management/commands/__init__.py
```

- [ ] **Étape 2 : Créer la commande**

Créer `apps/vendors/management/commands/vectorize_vendors.py` :

```python
from django.core.management.base import BaseCommand
from apps.vendors.embedding import vectorize_vendor
from apps.vendors.models import VendorProfile


class Command(BaseCommand):
    help = 'Vectorise les profils prestataires pour la recherche sémantique'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Re-vectorise tous les profils, même ceux déjà vectorisés',
        )

    def handle(self, *args, **options):
        if options['all']:
            qs = VendorProfile.objects.prefetch_related('service_types').order_by('pk')
        else:
            qs = VendorProfile.objects.filter(
                embedding__isnull=True
            ).prefetch_related('service_types').order_by('pk')

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Aucun profil à vectoriser.'))
            return

        done = 0
        failed = 0
        for i, vendor in enumerate(qs, 1):
            success = vectorize_vendor(vendor.pk)
            if success:
                done += 1
                self.stdout.write(f'{i}/{total} — {vendor.business_name[:50]} ... OK')
            else:
                failed += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'{i}/{total} — {vendor.business_name[:50]} ... ÉCHEC (clé absente ou erreur API)'
                    )
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'{done} vectorisé{"s" if done != 1 else ""}, {failed} échec{"s" if failed != 1 else ""}.')
        )
```

- [ ] **Étape 3 : Vérifier l'aide de la commande**

```bash
python manage.py vectorize_vendors --help
```

Résultat attendu : affiche la description et l'option `--all`.

- [ ] **Étape 4 : Tester la commande sans clé**

```bash
python manage.py vectorize_vendors
```

Résultat attendu : tous les profils marqués ÉCHEC avec "(clé absente ou erreur API)" — comportement correct sans `GROQ_API_KEY` dans `.env`.

- [ ] **Étape 5 : Montrer le diff et proposer le commit — attendre approbation**

Message de commit proposé : `feat: commande vectorize_vendors pour batch d'embeddings`

---

## Task 7 : Interface admin — boutons vectorisation

**Files:**
- Modify: `apps/accounts/admin_views.py`
- Modify: `apps/accounts/urls.py`
- Modify: `templates/accounts/admin/vendor_list.html`
- Modify: `templates/accounts/admin/vendor_detail.html`

- [ ] **Étape 1 : Ajouter les deux vues dans admin_views.py**

Dans `apps/accounts/admin_views.py`, ajouter l'import `require_POST` en haut du fichier :

```python
from django.views.decorators.http import require_POST
```

Puis ajouter les deux vues à la fin de la section `# ========== GESTION DES PRESTATAIRES ==========` (après toutes les vues vendor existantes) :

```python
@require_POST
@admin_required
def vectorize_all_vendors_view(request):
    """Vectorise tous les profils sans embedding."""
    from apps.vendors.embedding import vectorize_pending_vendors
    count = vectorize_pending_vendors()
    if count > 0:
        messages.success(request, f'{count} profil{"s" if count != 1 else ""} vectorisé{"s" if count != 1 else ""}.')
    else:
        messages.info(request, 'Aucun profil à vectoriser (tous déjà vectorisés ou clé GROQ_API_KEY absente).')
    return redirect('accounts:admin_vendor_list')


@require_POST
@admin_required
def vectorize_single_vendor_view(request, pk):
    """Vectorise un profil prestataire spécifique."""
    from apps.vendors.embedding import vectorize_vendor
    success = vectorize_vendor(pk)
    if success:
        messages.success(request, 'Profil vectorisé avec succès.')
    else:
        messages.error(request, 'Vectorisation échouée. Vérifiez que GROQ_API_KEY est configurée.')
    return redirect('accounts:admin_vendor_detail', pk=pk)
```

- [ ] **Étape 2 : Ajouter les routes dans urls.py**

Dans `apps/accounts/urls.py`, dans la section `# Gestion des prestataires`, ajouter les deux nouvelles routes **avant** la route `admin/vendors/<int:pk>/` pour éviter toute ambiguïté :

```python
    # Gestion des prestataires
    path('admin/vendors/', admin_views.vendor_list, name='admin_vendor_list'),
    path('admin/vendors/create/', admin_views.vendor_create, name='admin_vendor_create'),
    path('admin/vendors/vectorize-all/', admin_views.vectorize_all_vendors_view, name='admin_vendor_vectorize_all'),
    path('admin/vendors/<int:pk>/vectorize/', admin_views.vectorize_single_vendor_view, name='admin_vendor_vectorize'),
    path('admin/vendors/<int:pk>/', admin_views.vendor_detail, name='admin_vendor_detail'),
    path('admin/vendors/<int:pk>/edit/', admin_views.vendor_edit, name='admin_vendor_edit'),
    # ... reste des routes inchangées
```

La route `vectorize-all/` doit être placée avant `<int:pk>/` (déjà le cas puisque les routes textuelles ne matchent pas `<int:pk>`).

- [ ] **Étape 3 : Mettre à jour la vue vendor_list admin pour le compteur**

Dans `apps/accounts/admin_views.py`, modifier la fonction `vendor_list` (section GESTION DES PRESTATAIRES) pour ajouter deux variables au contexte :

```python
@admin_required
def vendor_list(request):
    """Liste des prestataires"""
    vendors = VendorProfile.objects.prefetch_related('cities', 'service_types').order_by('-created_at')
    is_active = request.GET.get('is_active')
    if is_active == '1':
        vendors = vendors.filter(is_active=True)
    elif is_active == '0':
        vendors = vendors.filter(is_active=False)
    paginator = Paginator(vendors, 20)
    vendors = paginator.get_page(request.GET.get('page'))
    service_types = ServiceType.objects.all().order_by('name')
    cities = City.objects.filter(is_active=True).order_by('name')
    total_vendors_count = VendorProfile.objects.count()
    non_vectorized_count = VendorProfile.objects.filter(embedding__isnull=True).count()
    return render(request, 'accounts/admin/vendor_list.html', {
        'vendors': vendors,
        'selected_is_active': is_active,
        'service_types': service_types,
        'cities': cities,
        'total_vendors_count': total_vendors_count,
        'non_vectorized_count': non_vectorized_count,
    })
```

- [ ] **Étape 4 : Ajouter le bouton dans vendor_list.html**

Dans `templates/accounts/admin/vendor_list.html`, trouver la div `.a-page-hd` (lignes 6-17).  
Modifier le contenu de cette div pour ajouter le bouton vectorisation à côté du bouton "Ajouter" :

```html
<div class="a-page-hd">
  <div>
    <h1 class="a-page-title">Prestataires</h1>
    <p class="a-page-sub">{{ vendors.paginator.count }} professionnel{{ vendors.paginator.count|pluralize }}</p>
  </div>
  <div style="display:flex; gap:.5rem; align-items:center;">
    {% if non_vectorized_count > 0 %}
    <form method="post" action="{% url 'accounts:admin_vendor_vectorize_all' %}">
      {% csrf_token %}
      <button type="submit" class="a-btn a-btn-ghost" style="font-size:.72rem; white-space:nowrap;">
        ↺ Vectoriser ({{ non_vectorized_count }}/{{ total_vendors_count }})
      </button>
    </form>
    {% endif %}
    <a href="{% url 'accounts:admin_vendor_create' %}" class="a-btn a-btn-primary">
      <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
      </svg>
      Ajouter
    </a>
  </div>
</div>
```

- [ ] **Étape 5 : Ajouter le badge + bouton dans vendor_detail.html**

Dans `templates/accounts/admin/vendor_detail.html`, trouver la div "Actions" dans la colonne droite (autour de la ligne 140). Ajouter le bloc vectorisation **à la fin** du `a-card-body` des actions, après le bouton "Voir le profil public" :

```html
      <div class="a-card">
        <div class="a-card-head"><span class="a-card-label">Actions</span></div>
        <div class="a-card-body" style="display:flex; flex-direction:column; gap:.5rem;">
          <a href="{% url 'accounts:admin_vendor_edit' vendor.pk %}" class="a-btn a-btn-primary" style="justify-content:center;">
            Modifier
          </a>
          <form method="post" action="{% url 'accounts:admin_vendor_toggle_active' vendor.pk %}">
            {% csrf_token %}
            <button type="submit" class="a-btn a-btn-ghost" style="width:100%; justify-content:center;">
              {% if vendor.is_active %}Désactiver{% else %}Activer{% endif %}
            </button>
          </form>
          <a href="{% url 'vendors:vendor_detail' vendor.pk %}" target="_blank"
             class="a-btn a-btn-ghost" style="justify-content:center;">
            Voir le profil public ↗
          </a>
          <!-- Embedding -->
          <div style="padding-top:.5rem; border-top:1px solid rgba(0,0,0,.06); margin-top:.25rem;">
            {% if vendor.embedding %}
            <div style="display:flex; align-items:center; gap:.375rem; margin-bottom:.375rem;">
              <span style="width:.45rem; height:.45rem; border-radius:50%; background:#2ecc71; flex-shrink:0;"></span>
              <span style="font-size:.65rem; color:var(--muted);">Vectorisé · {{ vendor.embedding_updated_at|timesince }}</span>
            </div>
            <form method="post" action="{% url 'accounts:admin_vendor_vectorize' vendor.pk %}">
              {% csrf_token %}
              <button type="submit" class="a-btn a-btn-ghost" style="width:100%; justify-content:center; font-size:.72rem;">
                ↺ Re-vectoriser
              </button>
            </form>
            {% else %}
            <div style="display:flex; align-items:center; gap:.375rem; margin-bottom:.375rem;">
              <span style="width:.45rem; height:.45rem; border-radius:50%; background:#e74c3c; flex-shrink:0;"></span>
              <span style="font-size:.65rem; color:var(--muted);">Non vectorisé</span>
            </div>
            <form method="post" action="{% url 'accounts:admin_vendor_vectorize' vendor.pk %}">
              {% csrf_token %}
              <button type="submit" class="a-btn a-btn-primary" style="width:100%; justify-content:center; font-size:.72rem;">
                Vectoriser
              </button>
            </form>
            {% endif %}
          </div>
        </div>
      </div>
```

- [ ] **Étape 6 : Vérifier manuellement**

```bash
python manage.py runserver
```

1. Aller sur `/accounts/admin/vendors/` → le bouton "↺ Vectoriser (N/M)" apparaît si des profils ne sont pas vectorisés ✓
2. Cliquer sur un prestataire → dans la colonne Actions, voir le badge rouge "Non vectorisé" + bouton "Vectoriser" ✓
3. Cliquer "Vectoriser" → message d'erreur "Vectorisation échouée. Vérifiez que GROQ_API_KEY est configurée." (normal sans clé en dev) ✓
4. Cliquer "↺ Vectoriser (N/M)" → message "Aucun profil à vectoriser (tous déjà vectorisés ou clé GROQ_API_KEY absente)." ✓

- [ ] **Étape 7 : Montrer le diff et proposer le commit — attendre approbation**

```bash
rtk git diff apps/accounts/admin_views.py apps/accounts/urls.py templates/accounts/admin/vendor_list.html templates/accounts/admin/vendor_detail.html
```

Message de commit proposé : `feat: interface admin vectorisation — bouton liste + badge fiche prestataire`

---

## Après l'implémentation : activer en production

Une fois tous les commits en place, pour activer la recherche sémantique en prod :

1. Ajouter `GROQ_API_KEY=gsk_xxxx` dans les variables d'environnement de production (Neon/Railway)
2. Se connecter à l'interface admin → `/accounts/admin/vendors/`
3. Cliquer "↺ Vectoriser (N/N)" pour vectoriser tous les profils existants
4. Tester la recherche sur `lysangels.com/prestataires/?search=gateaux`
