#!/usr/bin/env python
"""
SCRIPT UNIQUE DE POPULATION DE LA BASE DE DONNÉES - LysAngels
Ce script consolide tous les scripts de peuplement en un seul fichier.
Il crée toutes les données de test nécessaires pour développer et tester la plateforme.

Usage:
    python populate_database.py              # Sans images
    python populate_database.py --images     # Avec téléchargement d'images depuis Unsplash

Ordre d'exécution:
    1. Référentiels (villes, quartiers, services, événements)
    2. Abonnements
    3. Utilisateurs (admin, clients, prestataires)
    4. Profils prestataires avec portfolios
    5. Images de portfolio (optionnel, nécessite connexion internet)
    6. Projets et demandes de devis (optionnel)
"""
import os
import sys
import django
import random
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lysangels.settings')
django.setup()

from apps.accounts.models import User
from apps.vendors.models import SubscriptionTier, ServiceType, VendorProfile, VendorImage
from apps.projects.models import EventType, Project
from apps.proposals.models import ProposalRequest
from apps.core.models import City, Quartier


# ============================================================================
# DONNÉES DE RÉFÉRENCE
# ============================================================================

QUARTIERS_DATA = {
    'Lomé': [
        'Tokoin', 'Hanoukopé', 'Adidogomé', 'Bè', 'Nyékonakpoè', 'Agoè',
        'Hédzranawoé', 'Avedji', 'Légbassito', 'Amadahomé', 'Amoutivé',
        'Cacaveli', 'Djidjolé', 'Gbényédzi', 'Aflao Sagbado'
    ],
    'Kara': [
        'Centre-ville', 'Tchaoudjo', 'Sarakawa', 'Lassa', 'Pya',
        'Kpaha', 'Défale', 'Katomè'
    ],
    'Sokodé': [
        'Centre-ville', 'Kpangalam', 'Katchamba', 'Gbangbara', 'Komah',
        'Aledjo', 'Didaoure', 'Tchitchao'
    ],
    'Atakpamé': [
        'Centre-ville', 'Agbandi', 'Adeta', 'Kpodzi', 'Akpare'
    ],
    'Kpalimé': [
        'Centre-ville', 'Tomegbé', 'Kuma Apoti', 'Atsavé', 'Kpélé Élé'
    ],
    'Dapaong': [
        'Centre-ville', 'Nawaré', 'Kountoiré', 'Nawalbou', 'Bombouaka'
    ],
    'Tsévié': [
        'Centre-ville', 'Davié', 'Kélégougan', 'Mission Tové'
    ],
    'Aného': [
        'Centre-ville', 'Glidji', 'Anexo', 'Akodesséwa'
    ],
    'Bassar': [
        'Centre-ville', 'Kabou', 'Bangéli', 'Dimouri'
    ],
}

SERVICE_TYPES_DATA = [
    {'name': 'Salle de réception', 'icon': 'building'},
    {'name': 'Traiteur', 'icon': 'utensils'},
    {'name': 'Décoration', 'icon': 'palette'},
    {'name': 'Photographe', 'icon': 'camera'},
    {'name': 'Vidéaste', 'icon': 'video'},
    {'name': 'DJ / Musique', 'icon': 'music'},
    {'name': 'Animation', 'icon': 'gamepad'},
    {'name': 'Maquillage / Coiffure', 'icon': 'scissors'},
    {'name': 'Pâtisserie', 'icon': 'cake'},
    {'name': 'Location matériel', 'icon': 'boxes'},
    {'name': 'Transport', 'icon': 'car'},
    {'name': 'Fleuriste', 'icon': 'flower'},
]

EVENT_TYPES_DATA = [
    'Mariage',
    'Anniversaire',
    'Baptême',
    'Fiançailles',
    'Conférence',
    'Séminaire',
    'Gala',
    'Lancement de produit',
    'Retraite',
    'Autre',
]

SUBSCRIPTION_TIERS_DATA = [
    {
        'name': 'Gratuit',
        'slug': 'free',
        'price_monthly': 0,
        'display_priority': 2,
        'is_visible_in_list': False,
        'max_images': 3,
        'description': 'Profil basique invisible dans les listes publiques. Visible uniquement lors de recherches spécifiques.'
    },
    {
        'name': 'Standard',
        'slug': 'standard',
        'price_monthly': 5000,
        'display_priority': 1,
        'is_visible_in_list': True,
        'max_images': 10,
        'description': 'Visible dans les listes publiques. Jusqu\'à 10 photos. Peut répondre aux demandes de devis.'
    },
    {
        'name': 'Premium',
        'slug': 'premium',
        'price_monthly': 15000,
        'display_priority': 0,
        'is_visible_in_list': True,
        'max_images': 999,
        'description': 'Priorité d\'affichage maximale. Photos illimitées. Badge Premium. Statistiques avancées.'
    }
]

# Noms togolais pour les utilisateurs
PRENOMS_TOGOLAIS = [
    'Kofi', 'Ama', 'Yao', 'Akosua', 'Kwame', 'Abla', 'Koffi', 'Edem',
    'Sena', 'Dela', 'Mawuli', 'Afi', 'Koku', 'Ami', 'Kossi', 'Adjoa',
    'Kodjo', 'Akua', 'Kwasi', 'Afua', 'Kwabena', 'Adwoa', 'Kwaku', 'Afia',
    'Yaw', 'Esi', 'Fiifi', 'Efua', 'Kobi', 'Araba', 'Kwamina', 'Aba',
    'Ebo', 'Akuba', 'Kwesi', 'Ekua', 'Kobina', 'Amba', 'Komla', 'Ayawa',
    'Mensah', 'Ekuwa', 'Kwadwo', 'Abena', 'Kwaw', 'Adoma', 'Poku', 'Efie',
    'Nii', 'Akos'
]

NOMS_TOGOLAIS = [
    'Mensah', 'Agbodza', 'Koffi', 'Addo', 'Tetteh', 'Kpakpo', 'Dzogbede',
    'Amegashie', 'Ahiavor', 'Nyaku', 'Kpodo', 'Attipoe', 'Kouma', 'Deku',
    'Gbedemah', 'Akoto', 'Boateng', 'Asante', 'Annan', 'Appiah'
]

# Descriptions par type de service
DESCRIPTIONS_SERVICES = {
    'Photographe': [
        "Photographe professionnel avec 8 ans d'expérience dans les événements.",
        "Expert en photographie de mariage et événements corporatifs.",
        "Spécialiste de la photographie artistique pour vos moments précieux.",
        "Photographe événementiel spécialisé. Matériel haute définition. Retouche photos incluse.",
        "Studio photo professionnel. Shooting événements, mariages, portraits.",
    ],
    'Vidéaste': [
        "Vidéaste créatif spécialisé dans les films de mariage cinématographiques.",
        "Production vidéo professionnelle pour tous types d'événements.",
        "Expert en montage et post-production pour des vidéos inoubliables.",
        "Couverture vidéo complète avec drone. Style documentaire et artistique.",
    ],
    'Traiteur': [
        "Service traiteur haut de gamme avec cuisine locale et internationale.",
        "Traiteur spécialisé dans les grands événements et réceptions.",
        "Cuisine authentique togolaise pour vos événements traditionnels.",
        "Menu personnalisé selon vos préférences. Équipe expérimentée.",
    ],
    'DJ / Musique': [
        "DJ professionnel pour animer vos soirées avec style.",
        "Animation musicale tous genres pour des événements mémorables.",
        "Expert en ambiance musicale adaptée à chaque type d'événement.",
        "Sonorisation professionnelle et éclairage. Playlist personnalisée.",
    ],
    'Décoration': [
        "Décorateur d'intérieur spécialisé dans les événements élégants.",
        "Création de décors sur mesure pour des événements inoubliables.",
        "Expert en décoration florale et mise en scène d'événements.",
        "Design événementiel moderne et traditionnel. Matériel premium.",
    ],
    'Salle de réception': [
        "Magnifique salle de réception pouvant accueillir jusqu'à 500 personnes.",
        "Espace moderne et climatisé pour vos événements professionnels.",
        "Salle polyvalente avec équipements audiovisuels inclus.",
        "Grand espace modulable avec jardin. Parking disponible.",
    ],
    'Animation': [
        "Animateur professionnel pour des événements dynamiques et joyeux.",
        "Animation pour enfants et adultes avec jeux et activités.",
        "Expert en animation d'événements corporatifs et team building.",
    ],
    'Maquillage / Coiffure': [
        "Maquilleuse professionnelle spécialisée dans les mariages.",
        "Expert en coiffure et maquillage pour tous types d'événements.",
        "Service beauté complet pour la mariée et ses demoiselles d'honneur.",
    ],
    'Pâtisserie': [
        "Pâtissier créatif pour des gâteaux de mariage spectaculaires.",
        "Spécialiste en pâtisserie française et desserts personnalisés.",
        "Création de gâteaux sur mesure pour tous vos événements.",
    ],
    'Location matériel': [
        "Location de matériel événementiel: chaises, tables, tentes, etc.",
        "Large choix d'équipements pour réussir vos événements.",
        "Service de location avec livraison et installation incluses.",
    ],
    'Transport': [
        "Service de transport VIP pour mariages et événements spéciaux.",
        "Flotte de véhicules de luxe avec chauffeurs professionnels.",
        "Transport de groupes pour séminaires et événements d'entreprise.",
    ],
    'Fleuriste': [
        "Créations florales sur mesure pour des événements élégants.",
        "Fleuriste expert en compositions pour mariages et cérémonies.",
        "Décoration florale haut de gamme pour tous types d'événements.",
    ],
}

# Budget par type de service (min, max en FCFA)
BUDGET_RANGES = {
    'Photographe': (30000, 200000),
    'Vidéaste': (50000, 300000),
    'Traiteur': (100000, 1000000),
    'DJ / Musique': (25000, 150000),
    'Décoration': (50000, 500000),
    'Salle de réception': (100000, 800000),
    'Animation': (20000, 100000),
    'Maquillage / Coiffure': (10000, 80000),
    'Pâtisserie': (20000, 200000),
    'Location matériel': (30000, 300000),
    'Transport': (40000, 200000),
    'Fleuriste': (20000, 150000),
}


# ============================================================================
# FONCTIONS DE CRÉATION
# ============================================================================

def create_cities_quartiers():
    """Créer les villes et quartiers du Togo"""
    print("🏙️  CRÉATION DES VILLES ET QUARTIERS")
    print("=" * 60)
    
    city_count = 0
    quartier_count = 0
    
    for city_name, quartiers in QUARTIERS_DATA.items():
        city, created = City.objects.get_or_create(
            name=city_name,
            defaults={'is_active': True}
        )
        
        if created:
            city_count += 1
            print(f"✓ Ville créée: {city_name}")
        else:
            print(f"  Ville existante: {city_name}")
        
        for quartier_name in quartiers:
            quartier, created = Quartier.objects.get_or_create(
                city=city,
                name=quartier_name,
                defaults={'is_active': True}
            )
            
            if created:
                quartier_count += 1
    
    print(f"\n✅ {city_count} villes créées, {quartier_count} quartiers créés")
    print(f"📊 Total: {City.objects.count()} villes, {Quartier.objects.count()} quartiers\n")


def create_service_types():
    """Créer les types de services"""
    print("🎨 CRÉATION DES TYPES DE SERVICES")
    print("=" * 60)
    
    created_count = 0
    for st in SERVICE_TYPES_DATA:
        _, created = ServiceType.objects.get_or_create(
            name=st['name'],
            defaults={'icon': st['icon']}
        )
        if created:
            created_count += 1
            print(f"✓ Service créé: {st['name']}")
    
    print(f"\n✅ {created_count} types de services créés")
    print(f"📊 Total: {ServiceType.objects.count()} types de services\n")


def create_event_types():
    """Créer les types d'événements"""
    print("🎉 CRÉATION DES TYPES D'ÉVÉNEMENTS")
    print("=" * 60)
    
    created_count = 0
    for et in EVENT_TYPES_DATA:
        _, created = EventType.objects.get_or_create(name=et)
        if created:
            created_count += 1
            print(f"✓ Événement créé: {et}")
    
    print(f"\n✅ {created_count} types d'événements créés")
    print(f"📊 Total: {EventType.objects.count()} types d'événements\n")


def create_subscription_tiers():
    """Créer les paliers d'abonnement"""
    print("💳 CRÉATION DES ABONNEMENTS")
    print("=" * 60)
    
    created_count = 0
    updated_count = 0
    
    for tier_data in SUBSCRIPTION_TIERS_DATA:
        tier, created = SubscriptionTier.objects.update_or_create(
            slug=tier_data['slug'],
            defaults=tier_data
        )
        
        if created:
            created_count += 1
            print(f"✓ Abonnement créé: {tier.name} ({tier.price_monthly} FCFA/mois)")
        else:
            updated_count += 1
            print(f"  Abonnement existant: {tier.name}")
    
    print(f"\n✅ {created_count} abonnements créés, {updated_count} mis à jour")
    print(f"📊 Total: {SubscriptionTier.objects.count()} abonnements\n")


def create_admin_user():
    """Créer le superuser Django"""
    print("👑 CRÉATION DU SUPERUSER")
    print("=" * 60)
    
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@eventsusy.tg',
            password='admin123',
            first_name='Admin',
            last_name='System',
            user_type='admin'
        )
        print("✅ Superuser créé: admin / admin123")
    else:
        print("  Superuser existe déjà: admin")
    print()


def create_test_users():
    """Créer des utilisateurs de test (clients et prestataires basiques)"""
    print("👥 CRÉATION DES UTILISATEURS DE TEST")
    print("=" * 60)
    
    # Admin de test
    if not User.objects.filter(username='admin_test').exists():
        User.objects.create_user(
            username='admin_test',
            email='admin_test@eventsusy.tg',
            password='password123',
            first_name='Admin',
            last_name='Test',
            user_type='admin',
            city='Lomé',
            phone='+228 90 00 00 01'
        )
        print("✅ Admin test créé: admin_test / password123")
    
    # Clients de test
    clients_data = [
        ('client_test', 'client@test.com', 'Marie', 'Dupont', '+228 90 00 00 02'),
        ('client2_test', 'client2@test.com', 'Paul', 'Martin', '+228 90 00 00 03'),
        ('client3_test', 'client3@test.com', 'Ama', 'Koffi', '+228 90 00 00 04'),
    ]
    
    for username, email, firstname, lastname, phone in clients_data:
        if not User.objects.filter(username=username).exists():
            User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                first_name=firstname,
                last_name=lastname,
                user_type='client',
                city='Lomé',
                phone=phone
            )
            print(f"✅ Client créé: {username} / password123")
    
    print(f"\n📊 Total utilisateurs: {User.objects.count()}\n")


def create_vendors(count=50):
    """Créer des profils prestataires avec diversité"""
    print(f"🏢 CRÉATION DE {count} PRESTATAIRES")
    print("=" * 60)
    
    service_types = list(ServiceType.objects.all())
    cities = list(City.objects.all())
    tiers = list(SubscriptionTier.objects.all())
    
    if not service_types or not cities or not tiers:
        print("❌ Erreur: Créez d'abord les services, villes et abonnements!")
        return
    
    standard_tier = SubscriptionTier.objects.get(slug='standard')
    premium_tier = SubscriptionTier.objects.get(slug='premium')
    free_tier = SubscriptionTier.objects.get(slug='free')
    
    created = 0
    for i in range(count):
        username = f"vendor_{i+1}_{PRENOMS_TOGOLAIS[i % len(PRENOMS_TOGOLAIS)].lower()}"
        
        if User.objects.filter(username=username).exists():
            continue
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=f"{username}@eventsusy.tg",
            password='password123',
            first_name=PRENOMS_TOGOLAIS[i % len(PRENOMS_TOGOLAIS)],
            last_name=random.choice(NOMS_TOGOLAIS),
            user_type='provider',
            phone=f"+228 90 {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}"
        )
        
        # Choisir service(s)
        primary_service = random.choice(service_types)
        services = [primary_service]
        
        # 30% de chance d'avoir un 2ème service
        if random.random() < 0.3:
            other_services = [s for s in service_types if s != primary_service]
            if other_services:
                services.append(random.choice(other_services))
        
        # Choisir ville et quartier
        city = random.choice(cities)
        quartiers = list(city.quartiers.all())
        quartier = random.choice(quartiers) if quartiers else None
        
        # Description
        desc_options = DESCRIPTIONS_SERVICES.get(
            primary_service.name,
            ["Prestataire professionnel pour vos événements."]
        )
        description = random.choice(desc_options)
        
        # Budget
        min_budget, max_budget = BUDGET_RANGES.get(
            primary_service.name,
            (20000, 200000)
        )
        
        # Nom d'entreprise
        business_name = f"{primary_service.name} {user.first_name} {user.last_name}"
        
        # Abonnement (60% Standard, 30% Premium, 10% Gratuit)
        rand = random.random()
        if rand < 0.6:
            tier = standard_tier
        elif rand < 0.9:
            tier = premium_tier
        else:
            tier = free_tier
        
        # Créer le profil prestataire
        vendor = VendorProfile.objects.create(
            user=user,
            business_name=business_name,
            description=description,
            city=city,
            quartier=quartier,
            whatsapp=user.phone,
            min_budget=Decimal(str(min_budget)),
            max_budget=Decimal(str(max_budget)),
            subscription_tier=tier,
            is_active=True,
            is_featured=(random.random() < 0.15)  # 15% featured
        )
        
        vendor.service_types.set(services)
        created += 1
        
        if created % 10 == 0:
            print(f"  {created} prestataires créés...")
    
    print(f"\n✅ {created} prestataires créés au total")
    print(f"📊 Total profils: {VendorProfile.objects.count()}\n")


def create_sample_projects():
    """Créer quelques projets de test pour les clients"""
    print("📋 CRÉATION DE PROJETS DE TEST")
    print("=" * 60)
    
    clients = User.objects.filter(user_type='client')
    event_types = list(EventType.objects.all())
    cities = list(City.objects.all())
    
    if not clients.exists() or not event_types or not cities:
        print("⚠️  Pas de clients, types d'événements ou villes. Projets non créés.")
        return
    
    projects_data = [
        {
            'title': 'Mariage de Marie & Jean',
            'description': 'Nous organisons notre mariage traditionnel et civil. Recherchons traiteur, photographe et DJ.',
            'event_date': '2026-06-15',
            'event_time': '14:00',
            'location': 'Salle de réception Tokoin',
            'guest_count': 200,
            'budget_min': 500000,
            'budget_max': 1500000,
        },
        {
            'title': 'Anniversaire 50 ans',
            'description': 'Anniversaire surprise pour mes 50 ans. Ambiance chic et élégante.',
            'event_date': '2026-05-20',
            'event_time': '18:00',
            'location': 'Jardin privé Légbassito',
            'guest_count': 100,
            'budget_min': 300000,
            'budget_max': 800000,
        },
    ]
    
    created = 0
    for proj_data in projects_data:
        client = random.choice(clients)
        event_type = random.choice(event_types)
        city = random.choice(cities)
        
        if not Project.objects.filter(title=proj_data['title']).exists():
            Project.objects.create(
                client=client,
                event_type=event_type,
                city=city,
                **proj_data,
                status='published'
            )
            created += 1
            print(f"✓ Projet créé: {proj_data['title']}")
    
    print(f"\n✅ {created} projets créés")
    print(f"📊 Total projets: {Project.objects.count()}\n")


def display_summary():
    """Afficher un résumé final des données créées"""
    print("\n" + "=" * 60)
    print("✅ POPULATION DE LA BASE DE DONNÉES TERMINÉE!")
    print("=" * 60)
    print("\n📊 RÉSUMÉ DES DONNÉES:\n")
    
    print(f"   🏙️  Villes: {City.objects.count()}")
    print(f"   📍 Quartiers: {Quartier.objects.count()}")
    print(f"   🎨 Types de services: {ServiceType.objects.count()}")
    print(f"   🎉 Types d'événements: {EventType.objects.count()}")
    print(f"   💳 Abonnements: {SubscriptionTier.objects.count()}")
    print(f"   👥 Utilisateurs: {User.objects.count()}")
    print(f"      - Admins: {User.objects.filter(user_type='admin').count()}")
    print(f"      - Clients: {User.objects.filter(user_type='client').count()}")
    print(f"      - Prestataires: {User.objects.filter(user_type='provider').count()}")
    print(f"   🏢 Profils prestataires: {VendorProfile.objects.count()}")
    print(f"      - Gratuit: {VendorProfile.objects.filter(subscription_tier__slug='free').count()}")
    print(f"      - Standard: {VendorProfile.objects.filter(subscription_tier__slug='standard').count()}")
    print(f"      - Premium: {VendorProfile.objects.filter(subscription_tier__slug='premium').count()}")
    print(f"   📋 Projets: {Project.objects.count()}")
    
    print("\n🔑 COMPTES DE TEST:\n")
    print("   Admin:")
    print("      username: admin")
    print("      password: admin123\n")
    print("   Clients:")
    print("      username: client_test / client2_test / client3_test")
    print("      password: password123\n")
    print("   Prestataires:")
    print("      username: vendor_1_kofi / vendor_2_ama / ... (jusqu'à vendor_50_...)")
    print("      password: password123\n")
    
    print("=" * 60)
    print("🚀 La plateforme est prête pour le développement!")
    print("=" * 60)
    print()


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    """Exécuter toutes les étapes de population"""
    print("\n" + "=" * 60)
    print("🚀 POPULATION COMPLÈTE DE LA BASE DE DONNÉES - LysAngels")
    print("=" * 60)
    print()
    
    try:
        # 1. Référentiels géographiques
        create_cities_quartiers()
        
        # 2. Référentiels métier
        create_service_types()
        create_event_types()
        
        # 3. Abonnements
        create_subscription_tiers()
        
        # 4. Utilisateurs
        create_admin_user()
        create_test_users()
        
        # 5. Prestataires (50 par défaut)
        create_vendors(count=50)
        
        # 6. Projets de test (optionnel)
        create_sample_projects()
        
        # 7. Résumé
        display_summary()
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
