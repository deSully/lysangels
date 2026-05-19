from django.core.management.base import BaseCommand
from apps.vendors.embedding import EMBEDDING_MODEL


class Command(BaseCommand):
    help = 'Télécharge et met en cache le modèle d\'embedding sentence-transformers'

    def handle(self, *args, **options):
        self.stdout.write(f'Téléchargement du modèle {EMBEDDING_MODEL}...')
        from sentence_transformers import SentenceTransformer
        SentenceTransformer(EMBEDDING_MODEL)
        self.stdout.write(self.style.SUCCESS(f'Modèle {EMBEDDING_MODEL} prêt.'))
