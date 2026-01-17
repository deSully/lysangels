"""
Commande pour vérifier l'état des assets Cloudinary.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.vendors.models import VendorProfile


class Command(BaseCommand):
    help = 'Vérifie les assets Cloudinary et leur synchronisation avec la base de données'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list-all',
            action='store_true',
            help='Liste tous les assets sur Cloudinary',
        )
        parser.add_argument(
            '--fix-missing',
            action='store_true',
            help='Réupload les logos manquants depuis Unsplash',
        )

    def handle(self, *args, **options):
        list_all = options.get('list_all', False)
        fix_missing = options.get('fix_missing', False)

        self.stdout.write('=' * 60)
        self.stdout.write('VÉRIFICATION CLOUDINARY')
        self.stdout.write('=' * 60)

        # 1. Vérifier la configuration
        self.stdout.write('\n📋 Configuration:')
        storage_backend = getattr(settings, 'DEFAULT_FILE_STORAGE', 'Non défini')
        self.stdout.write(f'  DEFAULT_FILE_STORAGE: {storage_backend}')

        cloudinary_config = getattr(settings, 'CLOUDINARY_STORAGE', {})
        if cloudinary_config:
            cloud_name = cloudinary_config.get('CLOUD_NAME', 'Non défini')
            self.stdout.write(self.style.SUCCESS(f'  ✓ Cloud Name: {cloud_name}'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠ CLOUDINARY_STORAGE non configuré'))

        # 2. Statistiques base de données
        self.stdout.write('\n📊 Base de données:')
        total_vendors = VendorProfile.objects.count()
        vendors_with_logo = VendorProfile.objects.exclude(logo='').exclude(logo__isnull=True).count()
        vendors_without_logo = total_vendors - vendors_with_logo

        self.stdout.write(f'  Total prestataires: {total_vendors}')
        self.stdout.write(f'  Avec logo: {vendors_with_logo}')
        self.stdout.write(f'  Sans logo: {vendors_without_logo}')

        # 3. Vérifier les URLs des logos
        self.stdout.write('\n🔗 Analyse des URLs de logos:')
        cloudinary_logos = 0
        local_logos = 0
        other_logos = 0

        vendors_with_logos = VendorProfile.objects.exclude(logo='').exclude(logo__isnull=True)

        for vendor in vendors_with_logos:
            logo_url = str(vendor.logo.url) if vendor.logo else ''
            if 'cloudinary' in logo_url or 'res.cloudinary.com' in logo_url:
                cloudinary_logos += 1
            elif logo_url.startswith('/media/'):
                local_logos += 1
            elif logo_url:
                other_logos += 1

        self.stdout.write(f'  Logos Cloudinary: {cloudinary_logos}')
        self.stdout.write(f'  Logos locaux: {local_logos}')
        self.stdout.write(f'  Autres: {other_logos}')

        # 4. Lister les prestataires sans logo
        if vendors_without_logo > 0:
            self.stdout.write(f'\n⚠ Prestataires sans logo ({vendors_without_logo}):')
            no_logo_vendors = VendorProfile.objects.filter(logo='') | VendorProfile.objects.filter(logo__isnull=True)
            for vendor in no_logo_vendors[:20]:  # Limiter à 20
                self.stdout.write(f'  - {vendor.business_name} (ID: {vendor.id})')
            if vendors_without_logo > 20:
                self.stdout.write(f'  ... et {vendors_without_logo - 20} autres')

        # 5. Essayer de lister les assets Cloudinary (si l'API est disponible)
        if list_all:
            self.stdout.write('\n☁️ Assets sur Cloudinary:')
            try:
                import cloudinary
                import cloudinary.api

                # Configurer Cloudinary
                cloudinary.config(
                    cloud_name=cloudinary_config.get('CLOUD_NAME'),
                    api_key=cloudinary_config.get('API_KEY'),
                    api_secret=cloudinary_config.get('API_SECRET'),
                )

                # Récupérer les ressources
                result = cloudinary.api.resources(
                    type='upload',
                    max_results=500,
                    prefix='media/'  # Dossier par défaut de django-cloudinary-storage
                )

                resources = result.get('resources', [])
                self.stdout.write(f'  Total assets trouvés: {len(resources)}')

                # Grouper par type
                by_folder = {}
                for r in resources:
                    folder = r.get('folder', 'racine')
                    by_folder[folder] = by_folder.get(folder, 0) + 1

                for folder, count in sorted(by_folder.items()):
                    self.stdout.write(f'    {folder}: {count} fichiers')

                # Afficher les 10 derniers
                self.stdout.write('\n  10 derniers uploads:')
                for r in resources[:10]:
                    self.stdout.write(f'    - {r.get("public_id")} ({r.get("format")}, {r.get("bytes", 0) // 1024}KB)')

            except ImportError:
                self.stdout.write(self.style.WARNING('  ⚠ Module cloudinary non disponible pour l\'API'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erreur API Cloudinary: {str(e)}'))

        # 6. Réparer les logos manquants
        if fix_missing and vendors_without_logo > 0:
            self.stdout.write('\n🔧 Réparation des logos manquants...')
            self._fix_missing_logos()

        # Résumé
        self.stdout.write('\n' + '=' * 60)
        if cloudinary_logos == vendors_with_logo and vendors_without_logo == 0:
            self.stdout.write(self.style.SUCCESS('✅ Tout est synchronisé!'))
        else:
            self.stdout.write(self.style.WARNING(
                f'⚠ {vendors_without_logo} prestataires sans logo\n'
                f'   Utilisez --fix-missing pour réparer'
            ))

    def _fix_missing_logos(self):
        """Réupload les logos manquants depuis Unsplash."""
        import requests
        from django.core.files.base import ContentFile
        import random

        # URLs de fallback par défaut
        FALLBACK_URLS = [
            'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1478146896981-b80fe463b330?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1555244162-803834f70033?w=400&h=400&fit=crop',
        ]

        no_logo_vendors = VendorProfile.objects.filter(logo='') | VendorProfile.objects.filter(logo__isnull=True)
        fixed = 0

        for vendor in no_logo_vendors:
            try:
                url = random.choice(FALLBACK_URLS)
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    filename = f"vendor_{vendor.id}_logo.jpg"
                    vendor.logo.save(filename, ContentFile(response.content), save=True)
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Logo ajouté: {vendor.business_name}'))
                    fixed += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Échec: {vendor.business_name} - {str(e)[:30]}'))

        self.stdout.write(f'\n  {fixed} logos réparés')
