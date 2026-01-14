"""
Middleware pour gérer les restrictions d'abonnement
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone


class SubscriptionMiddleware:
    """
    Middleware qui vérifie l'état de l'abonnement des prestataires
    et applique les restrictions appropriées
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier si l'utilisateur est un prestataire
        if (
            request.user.is_authenticated and
            request.user.is_provider and
            hasattr(request.user, 'vendor_profile')
        ):
            vendor = request.user.vendor_profile

            # Si l'abonnement a expiré et que le prestataire est encore mis en avant
            if vendor.subscription_expires_at and vendor.is_featured:
                if timezone.now() >= vendor.subscription_expires_at:
                    # Retirer automatiquement la mise en avant
                    vendor.is_featured = False
                    vendor.save(update_fields=['is_featured'])

                    # Notifier l'utilisateur une seule fois par session
                    if not request.session.get('subscription_expired_notified'):
                        messages.warning(
                            request,
                            '⚠️ Votre abonnement a expiré. Votre profil n\'est plus mis en avant. '
                            'Renouvelez votre abonnement pour retrouver vos avantages Premium.'
                        )
                        request.session['subscription_expired_notified'] = True

            # Avertissement si l'abonnement expire dans moins de 7 jours
            elif vendor.subscription_expires_at and vendor.is_featured:
                days_remaining = (vendor.subscription_expires_at - timezone.now()).days
                if 0 < days_remaining <= 7:
                    # Notifier une seule fois par session
                    if not request.session.get('subscription_expiring_notified'):
                        messages.info(
                            request,
                            f'ℹ️ Votre abonnement expire dans {days_remaining} jour(s). '
                            f'Pensez à le renouveler pour conserver vos avantages.'
                        )
                        request.session['subscription_expiring_notified'] = True

        response = self.get_response(request)
        return response
