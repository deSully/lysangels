from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.vendors.models import Review


@receiver(post_save, sender=Review)
def update_vendor_rating_on_save(sender, instance, **kwargs):
    """Met à jour la note du prestataire après création/modification d'un avis"""
    instance.vendor.update_rating()


@receiver(post_delete, sender=Review)
def update_vendor_rating_on_delete(sender, instance, **kwargs):
    """Met à jour la note du prestataire après suppression d'un avis"""
    instance.vendor.update_rating()
