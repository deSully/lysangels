# Dashboard Analytique LysAngels — Design

## Objectif

Transformer le tableau de bord admin existant en un outil d'aide à la décision : tendances des demandes dans le temps, identification des services à recruter, suivi du pipeline commercial. La page reste unique, enrichie d'un sélecteur de période.

## Architecture

**Approche :** Extension de la vue et du template existants (`admin_dashboard` / `admin_dashboard.html`). Aucune nouvelle app, aucun nouveau endpoint.

**Transmission des données :** Les données pour les graphiques sont sérialisées en JSON côté Django et injectées dans le HTML via le tag `{% json_script %}`. Chart.js lit ces données au chargement de la page. Pas d'API, pas d'AJAX, pas de dépendances supplémentaires.

**Sélecteur de période :** Paramètre GET `?period=` acceptant `7`, `30`, `90`, `365` (défaut `30`). Toutes les stats sauf la courbe 12 mois s'adaptent à la période sélectionnée.

**Tech stack :** Django 6 / Python 3.12, Chart.js 4.x via CDN, vanilla JS.

---

## Sélecteur de période

4 boutons en haut de page : **7 jours · 30 jours · 90 jours · 12 mois**. Le bouton actif est mis en évidence. Chaque clic recharge la page avec `?period=X`.

---

## Section 1 — KPI Cards

4 cartes remplaçant les compteurs actuels :

| Carte | Calcul | Delta |
|---|---|---|
| Nouvelles demandes | `Project.objects.filter(status='new').count()` | — |
| Demandes reçues | projets créés sur la période | vs période précédente identique |
| Prestataires actifs | `VendorProfile.objects.filter(is_active=True).count()` | — |
| Taux de traitement | `closed / total` sur la période (%) | vs période précédente |

**Delta :** comparaison avec la période précédente de même durée (ex : si period=30, on compare les 30 derniers jours aux 30 jours d'avant). Affiché en vert si positif, rouge si négatif.

---

## Section 2 — Courbe des demandes (12 mois fixes)

**Type :** Line chart Chart.js.

**Données :** Nombre de demandes créées par mois sur les 12 derniers mois calendaires, indépendamment du sélecteur de période.

**Calcul Django :**
```python
from django.db.models.functions import TruncMonth
from django.db.models import Count

data = (
    Project.objects
    .filter(created_at__gte=twelve_months_ago)
    .annotate(month=TruncMonth('created_at'))
    .values('month')
    .annotate(count=Count('id'))
    .order_by('month')
)
```

Les mois sans demande sont comblés avec 0 pour une courbe continue.

**Utilité :** Révèle la saisonnalité (mariages, fêtes de fin d'année, rentrée…).

---

## Section 3 — Services demandés vs couverts

**Type :** Horizontal bar chart double (Chart.js grouped bar, horizontal).

**Données (sur toute la vie de la plateforme, pas filtré par période) :**
- Barre A : nombre de projets ayant demandé ce service (`Project.services_needed`)
- Barre B : nombre de prestataires actifs proposant ce service (`VendorProfile.service_types` + `is_active=True`)

**Calcul Django :**
```python
from apps.vendors.models import ServiceType

service_stats = []
for st in ServiceType.objects.all():
    demanded = st.projects.count()
    covered = st.vendors.filter(is_active=True).count()
    service_stats.append({
        'name': st.name,
        'demanded': demanded,
        'covered': covered,
    })
# Tri par demandes décroissantes
service_stats.sort(key=lambda x: x['demanded'], reverse=True)
```

**Lecture :** Un service avec beaucoup de demandes et peu de prestataires = priorité de recrutement.

---

## Section 4 — Types d'événements

**Type :** Donut chart Chart.js.

**Données :** Répartition des projets par `event_type` sur la période sélectionnée. Les projets sans event_type sont groupés sous "Non précisé".

**Calcul Django :**
```python
Project.objects
    .filter(created_at__gte=period_start)
    .values('event_type__name')
    .annotate(count=Count('id'))
    .order_by('-count')
```

---

## Section 5 — Pipeline (statuts)

**Type :** Barres de progression CSS (pas de Chart.js — plus lisible pour 4 valeurs fixes).

**Données :** Répartition des projets par statut sur la période sélectionnée.

| Statut | Couleur |
|---|---|
| Nouvelle demande | orange `var(--terra)` |
| Contacté | bleu `#3B82F6` |
| En cours | vert `#16A34A` |
| Clôturé | gris `var(--muted)` |

Chaque barre affiche le nombre et le pourcentage.

---

## Section 6 — Top 5 villes

**Type :** Horizontal bar chart Chart.js.

**Données :** Les 5 villes générant le plus de demandes sur la période sélectionnée (`Project.city`). Les projets sans ville sont exclus.

```python
Project.objects
    .filter(created_at__gte=period_start, city__isnull=False)
    .values('city__name')
    .annotate(count=Count('id'))
    .order_by('-count')[:5]
```

---

## Layout de la page

```
[Sélecteur de période : 7j | 30j | 90j | 12 mois]

[KPI 1] [KPI 2] [KPI 3] [KPI 4]

[Courbe 12 mois — pleine largeur]

[Services demandés vs couverts (2/3)] [Donut types événements (1/3)]

[Pipeline statuts (1/2)] [Top 5 villes (1/2)]

[Demandes récentes (existant)] [Prestataires récents (existant)]
```

---

## Injection des données JSON

```django
{{ chart_trends|json_script:"data-trends" }}
{{ chart_services|json_script:"data-services" }}
{{ chart_events|json_script:"data-events" }}
{{ chart_cities|json_script:"data-cities" }}
```

Le JS lit ces blocs et instancie les graphiques Chart.js après le DOM ready.

---

## Chart.js

Chargé via CDN en bas du template `admin_dashboard.html` uniquement (pas dans `base_admin.html` pour ne pas pénaliser toutes les autres pages admin) :

```html
{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<script>/* initialisation des graphiques */</script>
{% endblock %}
```

---

## Fichiers modifiés

| Fichier | Changement |
|---|---|
| `apps/accounts/admin_views.py` | Réécriture de `admin_dashboard` : calcul des 6 sections selon `?period=` |
| `templates/accounts/admin_dashboard.html` | Refonte complète : sélecteur + KPIs + 4 graphiques + pipeline CSS + tableaux existants + Chart.js |

Aucun nouveau modèle, aucune migration.

---

## Règles métier

- Le sélecteur de période affecte toutes les sections **sauf** la courbe 12 mois (toujours sur 12 mois)
- La section "Services demandés vs couverts" est toujours sur toute la vie de la plateforme (pas de filtre période) — les gaps de recrutement sont structurels, pas conjoncturels
- Les projets sans `event_type` ou sans `city` sont exclus des graphiques correspondants (pas d'erreur, pas de catégorie "vide")
- Si aucune donnée sur la période → graphique vide avec message "Aucune donnée sur cette période"
- Period par défaut : 30 jours
