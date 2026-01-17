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
from io import BytesIO

User = get_user_model()

DEFAULT_PASSWORD = 'password123'


class Command(BaseCommand):
    help = 'Charge des prestataires de démonstration pour LysAngels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-images',
            action='store_true',
            help='Télécharge et upload les logos sur Cloudinary',
        )

    def handle(self, *args, **options):
        with_images = options.get('with_images', False)

        self.stdout.write('Chargement des prestataires de démonstration...\n')

        # Vérifier que les types de services existent
        if not ServiceType.objects.exists():
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

        # Créer ou récupérer l'abonnement gratuit
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

        # Prestataires de démonstration
        demo_vendors = [
            {
                'username': 'photo_elegance',
                'email': 'photo.elegance@demo.lysangels.tg',
                'first_name': 'Kodjo',
                'last_name': 'Mensah',
                'business_name': 'Photo Élégance',
                'description': 'Studio photo professionnel spécialisé dans les mariages et événements. '
                              'Plus de 10 ans d\'expérience dans la capture de vos moments précieux.',
                'service_type': 'Photographe',
                'whatsapp': '+228 90 12 34 56',
                'min_budget': 50000,
                'max_budget': 500000,
                'logo_url': 'https://images.unsplash.com/photo-1542038784456-1ea8e935640e?w=400&h=400&fit=crop',
            },
            {
                'username': 'dj_vibes_togo',
                'email': 'dj.vibes@demo.lysangels.tg',
                'first_name': 'Yao',
                'last_name': 'Amouzou',
                'business_name': 'DJ Vibes Togo',
                'description': 'DJ professionnel avec équipement son et lumière haut de gamme. '
                              'Ambiance garantie pour tous vos événements!',
                'service_type': 'DJ / Musique',
                'whatsapp': '+228 91 23 45 67',
                'min_budget': 100000,
                'max_budget': 300000,
                'logo_url': 'https://images.unsplash.com/photo-1571266028243-d220e7a45380?w=400&h=400&fit=crop',
            },
            {
                'username': 'saveurs_africa',
                'email': 'saveurs.africa@demo.lysangels.tg',
                'first_name': 'Ama',
                'last_name': 'Koffi',
                'business_name': 'Saveurs d\'Africa',
                'description': 'Service traiteur spécialisé dans la cuisine africaine et internationale. '
                              'Buffets, cocktails, repas assis pour tous vos événements.',
                'service_type': 'Traiteur',
                'whatsapp': '+228 92 34 56 78',
                'min_budget': 200000,
                'max_budget': 2000000,
                'logo_url': 'https://images.unsplash.com/photo-1555244162-803834f70033?w=400&h=400&fit=crop',
            },
            {
                'username': 'deco_magic',
                'email': 'deco.magic@demo.lysangels.tg',
                'first_name': 'Akossiwa',
                'last_name': 'Assogba',
                'business_name': 'Déco Magic Events',
                'description': 'Décoration événementielle créative et sur mesure. '
                              'Nous transformons vos rêves en réalité avec des décors uniques.',
                'service_type': 'Décoration',
                'whatsapp': '+228 93 45 67 89',
                'min_budget': 150000,
                'max_budget': 1500000,
                'logo_url': 'https://images.unsplash.com/photo-1478146896981-b80fe463b330?w=400&h=400&fit=crop',
            },
            {
                'username': 'patisserie_delice',
                'email': 'patisserie.delice@demo.lysangels.tg',
                'first_name': 'Edem',
                'last_name': 'Agbeko',
                'business_name': 'Pâtisserie Délice',
                'description': 'Gâteaux de mariage et pièces montées sur mesure. '
                              'Créations artistiques et saveurs raffinées pour vos célébrations.',
                'service_type': 'Pâtisserie',
                'whatsapp': '+228 94 56 78 90',
                'min_budget': 30000,
                'max_budget': 500000,
                'logo_url': 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&h=400&fit=crop',
            },
            {
                'username': 'video_pro_228',
                'email': 'video.pro@demo.lysangels.tg',
                'first_name': 'Kofi',
                'last_name': 'Agbodjan',
                'business_name': 'Vidéo Pro 228',
                'description': 'Vidéaste professionnel, captation et montage de qualité cinématographique. '
                              'Films de mariage, clips événementiels, drone.',
                'service_type': 'Vidéaste',
                'whatsapp': '+228 95 67 89 01',
                'min_budget': 80000,
                'max_budget': 600000,
                'logo_url': 'https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=400&h=400&fit=crop',
            },
        ]

        created_count = 0
        for vendor_data in demo_vendors:
            # Créer l'utilisateur
            user, user_created = User.objects.get_or_create(
                username=vendor_data['username'],
                defaults={
                    'email': vendor_data['email'],
                    'first_name': vendor_data['first_name'],
                    'last_name': vendor_data['last_name'],
                    'user_type': 'provider',
                    'is_verified': True,
                }
            )

            if user_created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()

            # Vérifier si le profil existe déjà
            if hasattr(user, 'vendor_profile'):
                self.stdout.write(f'  - {vendor_data["business_name"]} (existant)')
                continue

            # Récupérer le type de service
            try:
                service_type = ServiceType.objects.get(name=vendor_data['service_type'])
            except ServiceType.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'  ⚠ Service "{vendor_data["service_type"]}" non trouvé, ignoré'
                ))
                continue

            # Créer le profil prestataire
            profile = VendorProfile.objects.create(
                user=user,
                business_name=vendor_data['business_name'],
                description=vendor_data['description'],
                whatsapp=vendor_data['whatsapp'],
                min_budget=vendor_data['min_budget'],
                max_budget=vendor_data['max_budget'],
                subscription_tier=free_tier,
                city=lome,
                is_active=True,
            )

            # Ajouter le type de service
            profile.service_types.add(service_type)

            # Ajouter le pays
            profile.countries.add(togo)

            # Télécharger et uploader le logo si demandé
            if with_images and vendor_data.get('logo_url'):
                try:
                    response = requests.get(vendor_data['logo_url'], timeout=10)
                    if response.status_code == 200:
                        # Déterminer l'extension
                        content_type = response.headers.get('content-type', 'image/jpeg')
                        ext = 'jpg' if 'jpeg' in content_type else 'png'
                        filename = f"{vendor_data['username']}_logo.{ext}"

                        # Sauvegarder le logo (sera uploadé sur Cloudinary en prod)
                        profile.logo.save(filename, ContentFile(response.content), save=True)
                        self.stdout.write(f'    📷 Logo uploadé')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'    ⚠ Erreur logo: {str(e)[:50]}'))

            self.stdout.write(self.style.SUCCESS(f'  ✓ {vendor_data["business_name"]}'))
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n✅ {created_count} prestataires créés!'))

        if not with_images:
            self.stdout.write(self.style.NOTICE(
                '\n💡 Pour ajouter les logos, relancez avec: --with-images'
            ))
