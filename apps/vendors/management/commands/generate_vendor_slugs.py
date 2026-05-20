from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.vendors.models import VendorProfile


class Command(BaseCommand):
    help = 'Génère ou régénère les slugs URL pour tous les prestataires sans slug'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Régénère les slugs même pour les prestataires qui en ont déjà un',
        )

    def handle(self, *args, **options):
        force = options['force']
        qs = VendorProfile.objects.all() if force else VendorProfile.objects.filter(slug='')
        count = 0
        for vendor in qs.order_by('id'):
            old_slug = vendor.slug
            vendor.slug = ''  # force regeneration in save()
            vendor.save(update_fields=['slug'] if not force else None)
            if vendor.slug != old_slug:
                self.stdout.write(f'  {vendor.business_name}: {old_slug or "(vide)"} → {vendor.slug}')
                count += 1
        self.stdout.write(self.style.SUCCESS(f'{count} slug(s) mis à jour.'))
