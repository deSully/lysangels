"""
Commande pour charger des prestataires de démonstration.
Les logos sont uploadés sur Cloudinary automatiquement.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.vendors.models import ServiceType, VendorProfile, SubscriptionTier
from apps.core.models import Country, City
from django.core.files.base import ContentFile
import requests
import random

User = get_user_model()

DEFAULT_PASSWORD = 'password123'

# Prénoms togolais/africains
FIRST_NAMES_MALE = [
    'Kodjo', 'Kofi', 'Yao', 'Edem', 'Koffi', 'Mensah', 'Kwame', 'Kossi',
    'Afi', 'Komlan', 'Sena', 'Dodji', 'Esso', 'Foli', 'Gabin', 'Hervé',
    'Innocent', 'Jean', 'Komi', 'Luc', 'Marc', 'Nestor', 'Olivier', 'Pascal',
    'Romain', 'Serge', 'Théophile', 'Victor', 'William', 'Xavier', 'Yves', 'Zinsou'
]

FIRST_NAMES_FEMALE = [
    'Ama', 'Akua', 'Adjoa', 'Efua', 'Akossiwa', 'Ablavi', 'Kafui', 'Esi',
    'Afia', 'Dzifa', 'Enyonam', 'Mawuena', 'Sena', 'Yawa', 'Abla', 'Akofa',
    'Délali', 'Elinam', 'Félicia', 'Grace', 'Henriette', 'Irène', 'Joséphine', 'Kékéli',
    'Laure', 'Marie', 'Nadège', 'Olivia', 'Pélagie', 'Rita', 'Sandra', 'Thérèse'
]

LAST_NAMES = [
    'Agbeko', 'Amouzou', 'Assogba', 'Ayivi', 'Bamisso', 'Dossou', 'Ekoué', 'Fiadjoe',
    'Gbeassor', 'Houndefo', 'Issa', 'Johnson', 'Klu', 'Lawson', 'Mensah', 'N\'Tcha',
    'Olympio', 'Pétey', 'Quashie', 'Radji', 'Soglo', 'Teko', 'Ugo', 'Vignon',
    'Wilson', 'Xomakou', 'Yovo', 'Zankli', 'Adjovi', 'Bodjona', 'Creppy', 'Degbe',
    'Eklu', 'Foley', 'Gaba', 'Houeto', 'Igue', 'Jato', 'Kokou', 'Loko'
]

# Quartiers de Lomé
QUARTIERS = [
    'Tokoin', 'Bè', 'Adidogomé', 'Agoè', 'Kodjoviakopé', 'Nyékonakpoè',
    'Hédzranawoé', 'Djidjolé', 'Gbossimé', 'Kégué', 'Adakpamé', 'Baguida',
    'Aflao', 'Cacavéli', 'Atikoumé', 'Agbalépédo', 'Amadahomé', 'Akodésséwa'
]

# Templates de description par service
DESCRIPTIONS = {
    'Photographe': [
        "Studio photo professionnel avec {years} ans d'expérience. Spécialisé dans les mariages, portraits et événements d'entreprise. Équipement haut de gamme et retouches incluses.",
        "Photographe passionné capturant vos moments précieux depuis {years} ans. Style moderne et créatif. Livraison rapide et album photo personnalisé.",
        "Expert en photographie événementielle. Couverture complète de vos cérémonies avec drone disponible. Plus de {events}+ événements réalisés.",
        "Photographe artistique spécialisé dans les mariages africains traditionnels et modernes. {years} ans d'expérience, travail soigné et professionnel.",
    ],
    'Vidéaste': [
        "Vidéaste professionnel avec équipement cinématographique. Films de mariage, clips événementiels, couverture drone. {years} ans d'expérience.",
        "Réalisation vidéo haut de gamme pour tous vos événements. Montage créatif, musique personnalisée, livraison sous 2 semaines.",
        "Spécialiste du film de mariage émouvant. Captation multi-caméras, drone 4K, montage professionnel. Plus de {events}+ mariages filmés.",
        "Studio de production vidéo complet. Publicités, événements corporate, mariages. Équipe expérimentée et créative.",
    ],
    'DJ / Musique': [
        "DJ professionnel avec {years} ans d'expérience. Sonorisation et éclairage inclus. Tous styles musicaux : afrobeat, coupé-décalé, RnB, variétés.",
        "Animation musicale pour mariages et soirées. Équipement son et lumière haut de gamme. Ambiance garantie !",
        "DJ polyvalent spécialisé dans les mariages. Plus de {events}+ soirées animées. Playlist personnalisée selon vos goûts.",
        "Orchestre live et DJ pour vos événements. Musique traditionnelle et moderne. Créons ensemble l'ambiance parfaite.",
    ],
    'Traiteur': [
        "Service traiteur spécialisé cuisine africaine et internationale. Buffets, cocktails, repas assis. Capacité jusqu'à 500 couverts.",
        "Traiteur événementiel avec {years} ans d'expérience. Menus personnalisés, produits frais et locaux. Service impeccable garanti.",
        "Cuisine traditionnelle togolaise revisitée pour vos événements. Buffets généreux, présentation soignée, service professionnel.",
        "Traiteur haut de gamme pour mariages et événements corporate. Chef expérimenté, carte variée, options végétariennes disponibles.",
    ],
    'Décoration': [
        "Décorateur événementiel créatif. Mariages, anniversaires, événements corporate. Création sur mesure selon vos envies et budget.",
        "Spécialiste de la décoration florale et événementielle. {years} ans d'expérience. Transformons vos rêves en réalité.",
        "Studio de décoration premium. Concepts uniques, matériaux de qualité, mise en place complète. Plus de {events}+ événements décorés.",
        "Décoration traditionnelle africaine et moderne. Tentes, pagodes, mobilier événementiel. Location et installation comprises.",
    ],
    'Pâtisserie': [
        "Pâtissière créative spécialisée dans les gâteaux de mariage. Pièces montées, wedding cakes, cupcakes personnalisés.",
        "Atelier de pâtisserie artisanale. Gâteaux sur mesure, saveurs originales, décoration artistique. {years} ans de passion.",
        "Cake designer professionnel. Créations uniques pour mariages et anniversaires. Dégustation gratuite sur rendez-vous.",
        "Pâtisserie événementielle haut de gamme. Buffets sucrés, pièces montées spectaculaires, macarons personnalisés.",
    ],
    'Maquillage / Coiffure': [
        "Maquilleuse professionnelle spécialisée mariées. Mise en beauté, coiffure, accessoires. {years} ans d'expérience.",
        "Studio beauté mobile pour vos événements. Maquillage, coiffure, nail art. Équipe de 3 professionnelles disponible.",
        "Spécialiste du maquillage africain traditionnel et moderne. Formation internationale, produits haut de gamme.",
        "Coiffeuse et maquilleuse pour mariages. Tresses, tissages, perruques, maquillage longue tenue. Essai inclus.",
    ],
    'Salle de réception': [
        "Salle de réception climatisée, capacité {capacity} personnes. Parking gratuit, cuisine équipée, sono incluse.",
        "Espace événementiel moderne avec jardin. Idéal pour mariages et séminaires. {capacity} places assises.",
        "Domaine de réception en bord de mer. Cadre exceptionnel pour vos événements. Capacité jusqu'à {capacity} invités.",
        "Salle polyvalente au cœur de Lomé. Modulable, climatisée, équipée. Location à partir de 4 heures.",
    ],
    'Location matériel': [
        "Location de matériel événementiel complet. Tables, chaises, vaisselle, nappes. Livraison et installation incluses.",
        "Tout pour vos événements : tentes, pagodes, mobilier, éclairage. Stock important, tarifs compétitifs.",
        "Location de matériel de sonorisation et éclairage professionnel. Technicien disponible sur demande.",
        "Vaisselle, verrerie et décoration de table à louer. Large choix, qualité premium, livraison Lomé et environs.",
    ],
    'Fleuriste': [
        "Fleuriste événementiel spécialisé dans les mariages. Bouquets, compositions, décoration florale complète.",
        "Atelier floral créatif. Fleurs fraîches et artificielles haut de gamme. {years} ans d'expérience en événementiel.",
        "Compositions florales sur mesure pour tous vos événements. Livraison et installation comprises.",
        "Fleuriste artistique. Créations originales, bouquets de mariée, décoration de tables et espaces.",
    ],
    'Animation': [
        "Animateur événementiel professionnel. MC bilingue, jeux, ambiance garantie. Plus de {events}+ événements animés.",
        "Équipe d'animation complète : animateur, danseuses traditionnelles, cracheur de feu. Spectacles sur mesure.",
        "Animation enfants et adultes. Clown, maquillage, jeux, mascotte. Forfaits anniversaires disponibles.",
        "Groupe folklorique traditionnel. Danses, percussions, costumes authentiques. Animation culturelle unique.",
    ],
    'Transport': [
        "Location de véhicules de luxe avec chauffeur. Limousines, berlines, 4x4 pour mariages et VIP.",
        "Service de transport événementiel. Navettes invités, voiture des mariés, coordination complète.",
        "Flotte de véhicules décorés pour mariages. Chauffeurs en costume, ponctualité garantie.",
        "Transport VIP et événementiel. Véhicules climatisés, chauffeurs professionnels, tarifs forfaitaires.",
    ],
}

# URLs d'images Unsplash par catégorie (URLs stables avec photo ID)
LOGO_URLS = {
    'Photographe': [
        'https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1606567595334-d39972c85dfd?w=400&h=400&fit=crop',
    ],
    'Vidéaste': [
        'https://images.unsplash.com/photo-1579566346927-c68383817a25?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1540655037529-dec987208707?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1616469829581-73993eb86b02?w=400&h=400&fit=crop',
    ],
    'DJ / Musique': [
        'https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1429962714451-bb934ecdc4ec?w=400&h=400&fit=crop',
    ],
    'Traiteur': [
        'https://images.unsplash.com/photo-1555244162-803834f70033?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400&h=400&fit=crop',
    ],
    'Décoration': [
        'https://images.unsplash.com/photo-1478146896981-b80fe463b330?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1510076857177-7470076d4098?w=400&h=400&fit=crop',
    ],
    'Pâtisserie': [
        'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1535141192574-5d4897c12636?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=400&h=400&fit=crop',
    ],
    'Maquillage / Coiffure': [
        'https://images.unsplash.com/photo-1487412947147-5cebf100ffc2?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?w=400&h=400&fit=crop',
    ],
    'Salle de réception': [
        'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1505236858219-8359eb29e329?w=400&h=400&fit=crop',
    ],
    'Location matériel': [
        'https://images.unsplash.com/photo-1530023367847-a683933f4172?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=400&h=400&fit=crop',
    ],
    'Fleuriste': [
        'https://images.unsplash.com/photo-1487530811176-3780de880c2d?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1455659817273-f96807779a8a?w=400&h=400&fit=crop',
    ],
    'Animation': [
        'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=400&h=400&fit=crop',
    ],
    'Transport': [
        'https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=400&h=400&fit=crop',
        'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400&h=400&fit=crop',
    ],
}

# Noms d'entreprises par service
BUSINESS_NAME_TEMPLATES = {
    'Photographe': ['Photo {}', 'Studio {}', '{} Photography', 'Objectif {}', '{} Images', 'Flash {}'],
    'Vidéaste': ['Vidéo {}', '{} Films', 'Studio {}', '{} Production', 'Ciné {}', '{} Motion'],
    'DJ / Musique': ['DJ {}', '{} Sound', '{} Music', 'Mix {}', '{} Vibes', 'Beat {}'],
    'Traiteur': ['Saveurs {}', '{} Traiteur', 'Délices {}', 'Chef {}', '{} Cuisine', 'Goût {}'],
    'Décoration': ['Déco {}', '{} Events', '{} Design', 'Art {}', '{} Créations', 'Style {}'],
    'Pâtisserie': ['Pâtisserie {}', '{} Cakes', 'Douceurs {}', 'Sweet {}', '{} Délices', 'Gâteaux {}'],
    'Maquillage / Coiffure': ['Beauty {}', '{} Glam', 'Style {}', '{} Look', 'Beauté {}', '{} Makeup'],
    'Salle de réception': ['Espace {}', 'Domaine {}', 'Salle {}', '{} Events', 'Le {}', 'Villa {}'],
    'Location matériel': ['{} Location', 'Équip {}', '{} Events', 'Matériel {}', '{} Services'],
    'Fleuriste': ['Fleurs {}', '{} Floral', 'Pétales {}', '{} Bouquets', 'Rose {}', '{} Garden'],
    'Animation': ['Anim {}', '{} Show', 'Fun {}', '{} Events', 'Happy {}', '{} Party'],
    'Transport': ['Trans {}', '{} Limousine', 'VIP {}', '{} Cars', 'Elite {}', '{} Drive'],
}

CREATIVE_WORDS = [
    'Élégance', 'Prestige', 'Royal', 'Premium', 'Excellence', 'Luxe', 'Or', 'Diamant',
    'Étoile', 'Soleil', 'Lumière', 'Harmonie', 'Passion', 'Rêve', 'Magic', 'Crystal',
    'Perle', 'Velours', 'Saphir', 'Jade', 'Ambre', 'Opale', 'Topaze', 'Rubis',
    'Azur', 'Eden', 'Paradise', 'Gloria', 'Victory', 'Success', 'Fortune', 'Zenith'
]


class Command(BaseCommand):
    help = 'Charge des prestataires de démonstration pour LysAngels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-images',
            action='store_true',
            help='Télécharge et upload les logos sur Cloudinary',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime tous les vendors de démo et leurs images Cloudinary avant de recréer',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Nombre de prestataires à créer (défaut: 100)',
        )

    def handle(self, *args, **options):
        with_images = options.get('with_images', False)
        reset = options.get('reset', False)
        count = options.get('count', 100)

        # Reset : supprimer tous les vendors de démo
        if reset:
            self._reset_demo_data()

        self.stdout.write(f'\nChargement de {count} prestataires de démonstration...\n')

        if with_images:
            self.stdout.write(self.style.SUCCESS('✓ Les logos seront téléchargés et stockés localement'))

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

        # Créer les abonnements
        free_tier, _ = SubscriptionTier.objects.get_or_create(
            slug='gratuit',
            defaults={
                'name': 'Gratuit',
                'price_monthly': 0,
                'display_priority': 2,
                'is_visible_in_list': True,
                'description': 'Abonnement gratuit de base',
                'max_images': 3
            }
        )

        standard_tier, _ = SubscriptionTier.objects.get_or_create(
            slug='standard',
            defaults={
                'name': 'Standard',
                'price_monthly': 5000,
                'display_priority': 1,
                'is_visible_in_list': True,
                'description': 'Abonnement standard',
                'max_images': 10
            }
        )

        premium_tier, _ = SubscriptionTier.objects.get_or_create(
            slug='premium',
            defaults={
                'name': 'Premium',
                'price_monthly': 15000,
                'display_priority': 0,
                'is_visible_in_list': True,
                'description': 'Abonnement premium avec priorité',
                'max_images': 30
            }
        )

        tiers = [free_tier, free_tier, free_tier, standard_tier, standard_tier, premium_tier]
        used_usernames = set()
        used_business_names = set()
        created_count = 0

        for i in range(count):
            # Choisir un service aléatoire
            service_type = random.choice(service_types)
            service_name = service_type.name

            # Générer un nom unique
            is_female = random.random() < 0.4
            first_name = random.choice(FIRST_NAMES_FEMALE if is_female else FIRST_NAMES_MALE)
            last_name = random.choice(LAST_NAMES)

            # Générer username unique
            base_username = f"{first_name.lower()}_{last_name.lower()}".replace("'", "").replace(" ", "_")
            username = base_username
            suffix = 1
            while username in used_usernames or User.objects.filter(username=username).exists():
                username = f"{base_username}_{suffix}"
                suffix += 1
            used_usernames.add(username)

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
                'Pâtisserie': (25000, 500000),
                'Maquillage / Coiffure': (20000, 150000),
                'Salle de réception': (200000, 2000000),
                'Location matériel': (50000, 500000),
                'Fleuriste': (30000, 400000),
                'Animation': (50000, 300000),
                'Transport': (50000, 400000),
            }
            min_b, max_b = budget_ranges.get(service_name, (50000, 500000))
            min_budget = random.randint(min_b // 10000, min_b // 5000) * 10000
            max_budget = random.randint(max_b // 2 // 10000, max_b // 10000) * 10000

            # Créer l'utilisateur
            email = f"{username}@demo.lysangels.tg"
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'user_type': 'provider',
                    'is_verified': True,
                }
            )

            if user_created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()

            # Vérifier si le profil existe déjà
            if hasattr(user, 'vendor_profile'):
                continue

            # Créer le profil prestataire
            quartier = random.choice(QUARTIERS)
            whatsapp = f"+228 9{random.randint(0,9)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}"

            profile = VendorProfile.objects.create(
                user=user,
                business_name=business_name,
                description=description,
                whatsapp=whatsapp,
                address=f"{quartier}, Lomé",
                min_budget=min_budget,
                max_budget=max_budget,
                subscription_tier=random.choice(tiers),
                city=lome,
                is_active=True,
            )

            # Ajouter le type de service (parfois plusieurs)
            profile.service_types.add(service_type)
            if random.random() < 0.2:  # 20% ont un 2e service
                other_service = random.choice(service_types)
                if other_service != service_type:
                    profile.service_types.add(other_service)

            # Ajouter le pays
            profile.countries.add(togo)

            # Télécharger et sauvegarder le logo si demandé
            if with_images:
                logo_urls = LOGO_URLS.get(service_name, [])
                if logo_urls:
                    try:
                        logo_url = random.choice(logo_urls)

                        # Télécharger l'image depuis Unsplash
                        response = requests.get(logo_url, timeout=15)
                        if response.status_code == 200:
                            filename = f"{username}_logo.jpg"

                            # Sauvegarder via le champ ImageField (stockage local ou R2)
                            profile.logo.save(filename, ContentFile(response.content), save=True)
                            self.stdout.write(self.style.SUCCESS(f'    ✓ Logo: {business_name}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'    ⚠ Échec téléchargement logo pour {business_name} (HTTP {response.status_code})'))
                    except requests.exceptions.Timeout:
                        self.stdout.write(self.style.WARNING(f'    ⚠ Timeout téléchargement logo pour {business_name}'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'    ⚠ Erreur logo pour {business_name}: {str(e)[:80]}'))

            created_count += 1
            if created_count % 10 == 0:
                self.stdout.write(f'  {created_count} prestataires créés...')

        self.stdout.write(self.style.SUCCESS(f'\n✅ {created_count} prestataires créés!'))
        self.stdout.write(f'🔑 Mot de passe: {DEFAULT_PASSWORD}')

        if not with_images:
            self.stdout.write(self.style.NOTICE(
                '\n💡 Pour ajouter les logos: python manage.py load_demo_vendors --with-images'
            ))

    def _reset_demo_data(self):
        """Supprime tous les vendors de démo et leurs fichiers."""
        self.stdout.write('🗑️  RESET: Suppression des données de démonstration...\n')

        # 1. Supprimer les profils vendors de démo (les fichiers sont supprimés automatiquement)
        self.stdout.write('  Suppression des profils prestataires de démo...')
        demo_vendors = VendorProfile.objects.filter(user__email__endswith='@demo.lysangels.tg')
        vendor_count = demo_vendors.count()

        # Supprimer les fichiers logo avant de supprimer les profils
        for vendor in demo_vendors:
            if vendor.logo:
                vendor.logo.delete(save=False)

        demo_vendors.delete()
        self.stdout.write(self.style.SUCCESS(f'    ✓ {vendor_count} profils supprimés'))

        # 2. Supprimer les utilisateurs de démo
        self.stdout.write('  Suppression des utilisateurs de démo...')
        demo_users = User.objects.filter(email__endswith='@demo.lysangels.tg')
        user_count = demo_users.count()
        demo_users.delete()
        self.stdout.write(self.style.SUCCESS(f'    ✓ {user_count} utilisateurs supprimés'))

        self.stdout.write(self.style.SUCCESS('\n✅ Reset terminé!'))
