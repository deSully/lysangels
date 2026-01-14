"""
Commande de management Django pour vérifier et gérer les abonnements expirés
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from apps.vendors.models import VendorProfile, SubscriptionTier


class Command(BaseCommand):
    help = 'Vérifie et désactive les prestataires dont l\'abonnement a expiré'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les actions sans les exécuter',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        self.stdout.write(self.style.SUCCESS(f'🔍 Vérification des abonnements expirés - {now.strftime("%d/%m/%Y %H:%M")}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN: Aucune modification ne sera effectuée\n'))

        # Trouver les prestataires avec abonnement expiré
        expired_vendors = VendorProfile.objects.filter(
            Q(subscription_expires_at__lt=now) &  # Date d'expiration passée
            Q(is_featured=True)  # Qui sont encore mis en avant
        ).select_related('user', 'subscription_tier')

        expired_count = expired_vendors.count()

        if expired_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ Aucun abonnement expiré trouvé'))
            return

        self.stdout.write(self.style.WARNING(f'⚠️  {expired_count} prestataire(s) avec abonnement expiré:\n'))

        for vendor in expired_vendors:
            days_expired = (now - vendor.subscription_expires_at).days

            self.stdout.write(f'   📍 {vendor.business_name}')
            self.stdout.write(f'      Utilisateur: {vendor.user.get_full_name()} ({vendor.user.email})')
            self.stdout.write(f'      Abonnement: {vendor.subscription_tier.name if vendor.subscription_tier else "Aucun"}')
            self.stdout.write(f'      Expiré depuis: {days_expired} jour(s)')

            if not dry_run:
                # Retirer la mise en avant
                vendor.is_featured = False
                vendor.save(update_fields=['is_featured'])
                self.stdout.write(self.style.SUCCESS(f'      ✓ Mise en avant retirée\n'))
            else:
                self.stdout.write(self.style.WARNING(f'      [DRY-RUN] Mise en avant serait retirée\n'))

        # Trouver les prestataires dont l'abonnement expire bientôt (dans les 7 jours)
        warning_date = now + timezone.timedelta(days=7)
        expiring_soon = VendorProfile.objects.filter(
            Q(subscription_expires_at__gt=now) &
            Q(subscription_expires_at__lt=warning_date) &
            Q(is_featured=True)
        ).select_related('user', 'subscription_tier')

        expiring_count = expiring_soon.count()

        if expiring_count > 0:
            self.stdout.write(self.style.WARNING(f'\n⏰ {expiring_count} abonnement(s) expirent dans les 7 prochains jours:\n'))

            for vendor in expiring_soon:
                days_remaining = (vendor.subscription_expires_at - now).days
                self.stdout.write(f'   📍 {vendor.business_name}')
                self.stdout.write(f'      Expire dans: {days_remaining} jour(s)')
                self.stdout.write(f'      Date d\'expiration: {vendor.subscription_expires_at.strftime("%d/%m/%Y")}')
                self.stdout.write(f'      Contact: {vendor.user.email}\n')

        if not dry_run and expired_count > 0:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Traitement terminé: {expired_count} prestataire(s) mis à jour'))
        elif dry_run and expired_count > 0:
            self.stdout.write(self.style.WARNING(f'\n⚠️  DRY-RUN terminé: {expired_count} prestataire(s) seraient mis à jour'))
