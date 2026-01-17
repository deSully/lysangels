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
