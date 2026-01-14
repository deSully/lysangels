"""
Script pour créer le pays Togo et assigner toutes les villes existantes au Togo
À exécuter après les migrations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lysangels.settings')
django.setup()

from apps.core.models import Country, City

# Créer le pays Togo
togo, created = Country.objects.get_or_create(
    code='TG',
    defaults={
        'name': 'Togo',
        'flag_emoji': '🇹🇬',
        'is_active': True,
        'display_order': 1
    }
)

if created:
    print(f"✅ Pays créé : {togo}")
else:
    print(f"ℹ️  Pays existant : {togo}")

# Assigner toutes les villes au Togo
cities_updated = City.objects.filter(country__isnull=True).update(country=togo)
print(f"✅ {cities_updated} ville(s) assignée(s) au Togo")

# Afficher toutes les villes
all_cities = City.objects.all()
print(f"\n📍 Villes au Togo ({all_cities.count()}) :")
for city in all_cities:
    print(f"   - {city}")
