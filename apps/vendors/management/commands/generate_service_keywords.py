import time
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.vendors.models import ServiceType


class Command(BaseCommand):
    help = 'Génère les mots-clés de recherche pour chaque type de service via Groq LLM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-génère même si des mots-clés existent déjà',
        )

    def handle(self, *args, **options):
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        if not api_key:
            self.stderr.write(self.style.ERROR('GROQ_API_KEY non configurée dans les settings.'))
            return

        if options['force']:
            services = ServiceType.objects.all().order_by('name')
        else:
            services = ServiceType.objects.filter(search_keywords='').order_by('name')

        total = services.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Tous les types de service ont déjà des mots-clés.'))
            return

        done = 0
        for i, service in enumerate(services, 1):
            self.stdout.write(f'{i}/{total} — {service.name}...')
            try:
                keywords = self._generate(api_key, service.name)
                service.search_keywords = keywords
                service.save(update_fields=['search_keywords'])
                self.stdout.write(self.style.SUCCESS(f'  → {keywords[:100]}'))
                done += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  → ÉCHEC : {e}'))
            if i < total:
                time.sleep(0.8)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'{done}/{total} type(s) traité(s).'))

    def _generate(self, api_key, service_name):
        prompt = (
            f'Tu es un assistant pour une marketplace événementielle en Afrique de l\'Ouest (Togo). '
            f'Génère 12 à 15 mots-clés en français qu\'un utilisateur pourrait taper pour rechercher '
            f'un prestataire de type "{service_name}". '
            f'Inclus des synonymes, des variantes avec et sans accents, et des termes courants locaux. '
            f'Réponds uniquement avec les mots-clés séparés par des virgules, en minuscules, sans explication ni ponctuation finale.'
        )
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3,
                'max_tokens': 200,
            },
            timeout=15,
        )
        resp.raise_for_status()
        raw = resp.json()['choices'][0]['message']['content'].strip().rstrip('.')
        return ', '.join(k.strip().lower() for k in raw.split(',') if k.strip())
