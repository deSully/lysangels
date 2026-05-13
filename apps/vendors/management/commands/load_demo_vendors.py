"""
Commande pour charger des prestataires de démonstration.
"""
from django.core.management.base import BaseCommand
from apps.vendors.models import ServiceType, VendorProfile
from apps.core.models import Country, City
import random

# Prénoms togolais/africains
FIRST_NAMES_MALE = [
    'Kodjo', 'Kofi', 'Yao', 'Edem', 'Koffi', 'Mensah', 'Kwame', 'Kossi',
    'Komlan', 'Sena', 'Dodji', 'Esso', 'Foli', 'Gabin', 'Hervé',
    'Innocent', 'Jean', 'Komi', 'Luc', 'Marc', 'Nestor', 'Olivier', 'Pascal',
]

FIRST_NAMES_FEMALE = [
    'Ama', 'Akua', 'Adjoa', 'Efua', 'Akossiwa', 'Ablavi', 'Kafui', 'Esi',
    'Afia', 'Dzifa', 'Enyonam', 'Mawuena', 'Sena', 'Yawa', 'Abla', 'Akofa',
    'Délali', 'Elinam', 'Félicia', 'Grace', 'Henriette', 'Irène', 'Joséphine',
]

LAST_NAMES = [
    'Agbeko', 'Amouzou', 'Assogba', 'Ayivi', 'Bamisso', 'Dossou', 'Ekoué', 'Fiadjoe',
    'Gbeassor', 'Houndefo', 'Issa', 'Johnson', 'Klu', 'Lawson', 'Mensah',
    'Olympio', 'Soglo', 'Teko', 'Vignon', 'Wilson', 'Yovo', 'Adjovi',
]

QUARTIERS = [
    'Tokoin', 'Bè', 'Adidogomé', 'Agoè', 'Kodjoviakopé', 'Nyékonakpoè',
    'Hédzranawoé', 'Djidjolé', 'Gbossimé', 'Kégué', 'Adakpamé', 'Baguida',
]

DESCRIPTIONS = {
    'Photographe': [
        "Studio photo professionnel avec {years} ans d'expérience. Spécialisé dans les mariages, portraits et événements d'entreprise.",
        "Photographe passionné capturant vos moments précieux depuis {years} ans. Style moderne et créatif.",
        "Expert en photographie événementielle. Plus de {events}+ événements réalisés.",
    ],
    'Vidéaste': [
        "Vidéaste professionnel avec équipement cinématographique. Films de mariage, clips événementiels. {years} ans d'expérience.",
        "Réalisation vidéo haut de gamme pour tous vos événements. Montage créatif, musique personnalisée.",
        "Spécialiste du film de mariage émouvant. Plus de {events}+ mariages filmés.",
    ],
    'DJ / Musique': [
        "DJ professionnel avec {years} ans d'expérience. Sonorisation et éclairage inclus.",
        "Animation musicale pour mariages et soirées. Équipement son et lumière haut de gamme.",
        "DJ polyvalent spécialisé dans les mariages. Plus de {events}+ soirées animées.",
    ],
    'Traiteur': [
        "Service traiteur spécialisé cuisine africaine et internationale. Buffets, cocktails, repas assis.",
        "Traiteur événementiel avec {years} ans d'expérience. Menus personnalisés, produits frais et locaux.",
        "Cuisine traditionnelle togolaise revisitée pour vos événements.",
    ],
    'Décoration': [
        "Décorateur événementiel créatif. Mariages, anniversaires, événements corporate.",
        "Spécialiste de la décoration florale et événementielle. {years} ans d'expérience.",
        "Studio de décoration premium. Plus de {events}+ événements décorés.",
    ],
}

BUSINESS_NAME_TEMPLATES = {
    'Photographe': ['Photo {}', 'Studio {}', '{} Photography', 'Objectif {}', '{} Images'],
    'Vidéaste': ['Vidéo {}', '{} Films', 'Studio {}', '{} Production', 'Ciné {}'],
    'DJ / Musique': ['DJ {}', '{} Sound', '{} Music', 'Mix {}', '{} Vibes'],
    'Traiteur': ['Saveurs {}', '{} Traiteur', 'Délices {}', 'Chef {}', '{} Cuisine'],
    'Décoration': ['Déco {}', '{} Events', '{} Design', 'Art {}', '{} Créations'],
}

CREATIVE_WORDS = [
    'Élégance', 'Prestige', 'Royal', 'Premium', 'Excellence', 'Luxe', 'Or', 'Diamant',
    'Étoile', 'Soleil', 'Lumière', 'Harmonie', 'Passion', 'Rêve', 'Magic', 'Crystal',
]


class Command(BaseCommand):
    help = 'Charge des prestataires de démonstration pour LysAngels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime tous les vendors de démo avant de recréer',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Nombre de prestataires à créer (défaut: 20)',
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)
        count = options.get('count', 20)

        if reset:
            self._reset_demo_data()

        self.stdout.write(f'\nChargement de {count} prestataires de démonstration...\n')

        # Vérifier que les types de services existent
        service_types = list(ServiceType.objects.all())
        if not service_types:
            self.stdout.write(self.style.ERROR(
                '❌ Aucun type de service trouvé. Exécutez d\'abord:\n'
                '   python manage.py load_service_types'
            ))
            return

        # Créer ou récupérer le pays Togo
        togo, _ = Country.objects.get_or_create(
            code='TG',
            defaults={'name': 'Togo', 'flag_emoji': '🇹🇬', 'is_active': True}
        )

        # Créer ou récupérer la ville Lomé
        lome, _ = City.objects.get_or_create(
            name='Lomé',
            defaults={'country': togo, 'is_active': True}
        )

        used_business_names = set(VendorProfile.objects.values_list('business_name', flat=True))
        created_count = 0

        for i in range(count):
            service_type = random.choice(service_types)
            service_name = service_type.name

            # Générer nom d'entreprise unique
            templates = BUSINESS_NAME_TEMPLATES.get(service_name, ['{} Events'])
            word = random.choice(CREATIVE_WORDS)
            business_name = random.choice(templates).format(word)
            suffix = 1
            while business_name in used_business_names:
                business_name = f"{random.choice(templates).format(word)} {suffix}"
                suffix += 1
            used_business_names.add(business_name)

            # Générer description
            years = random.randint(3, 15)
            events = random.randint(50, 500)
            capacity = random.choice([100, 150, 200, 300, 500])
            desc_templates = DESCRIPTIONS.get(service_name, ["Service professionnel de qualité. {years} ans d'expérience."])
            description = random.choice(desc_templates).format(years=years, events=events, capacity=capacity)

            # Budgets selon le service
            budget_ranges = {
                'Photographe': (50000, 500000),
                'Vidéaste': (80000, 600000),
                'DJ / Musique': (50000, 300000),
                'Traiteur': (100000, 2000000),
                'Décoration': (100000, 1500000),
            }
            min_b, max_b = budget_ranges.get(service_name, (50000, 500000))
            min_budget = random.randint(min_b // 10000, min_b // 5000) * 10000
            max_budget = random.randint(max_b // 2 // 10000, max_b // 10000) * 10000

            # Générer contact WhatsApp
            quartier = random.choice(QUARTIERS)
            whatsapp = f"+228 9{random.randint(0,9)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}"

            # Créer le profil prestataire
            profile = VendorProfile.objects.create(
                business_name=business_name,
                description=description,
                whatsapp=whatsapp,
                address=f"{quartier}, Lomé",
                min_budget=min_budget,
                max_budget=max_budget,
                city=lome,
                is_active=True,
                is_featured=random.random() < 0.2,  # 20% mis en avant
            )

            # Ajouter le type de service
            profile.service_types.add(service_type)
            if random.random() < 0.2:  # 20% ont un 2e service
                other_service = random.choice(service_types)
                if other_service != service_type:
                    profile.service_types.add(other_service)

            # Ajouter le pays
            profile.countries.add(togo)

            created_count += 1
            if created_count % 10 == 0:
                self.stdout.write(f'  {created_count} prestataires créés...')

        self.stdout.write(self.style.SUCCESS(f'\n✅ {created_count} prestataires créés!'))

    def _reset_demo_data(self):
        """Supprime tous les vendors de démo."""
        self.stdout.write('🗑️  RESET: Suppression des données de démonstration...\n')
        demo_vendors = VendorProfile.objects.filter(
            business_name__contains='Élégance'
        ) | VendorProfile.objects.filter(
            business_name__contains='Prestige'
        ) | VendorProfile.objects.filter(
            business_name__contains='Royal'
        )
        count = demo_vendors.count()
        demo_vendors.delete()
        self.stdout.write(self.style.SUCCESS(f'✓ {count} profils supprimés'))
