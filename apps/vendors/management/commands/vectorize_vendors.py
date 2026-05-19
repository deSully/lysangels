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
            success, error = vectorize_vendor(vendor.pk)
            if success:
                done += 1
                self.stdout.write(f'{i}/{total} — {vendor.business_name[:50]} ... OK')
            else:
                failed += 1
                self.stdout.write(
                    self.style.WARNING(f'{i}/{total} — {vendor.business_name[:50]} ... ÉCHEC : {error}')
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'{done} vectorisé{"s" if done != 1 else ""}, {failed} échec{"s" if failed != 1 else ""}.')
        )
