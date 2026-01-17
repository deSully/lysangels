"""
Commande pour charger les types d'événements.
"""
from django.core.management.base import BaseCommand
from apps.projects.models import EventType


class Command(BaseCommand):
    help = 'Charge les types d\'événements pour LysAngels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime tous les types d\'événements avant de les recharger',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Suppression des types d\'événements existants...')
            count = EventType.objects.count()
            EventType.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'  ✓ {count} types supprimés'))

        self.stdout.write('\nChargement des types d\'événements...\n')

        events = [
            {'name': 'Mariage', 'description': 'Célébration de mariage', 'icon': 'heart'},
            {'name': 'Anniversaire', 'description': 'Fête d\'anniversaire', 'icon': 'gift'},
            {'name': 'Baptême', 'description': 'Cérémonie de baptême', 'icon': 'baby'},
            {'name': 'Fiançailles', 'description': 'Cérémonie de fiançailles', 'icon': 'ring'},
            {'name': 'Conférence', 'description': 'Événement professionnel ou conférence', 'icon': 'briefcase'},
            {'name': 'Séminaire', 'description': 'Séminaire d\'entreprise', 'icon': 'users'},
            {'name': 'Gala', 'description': 'Soirée de gala', 'icon': 'champagne'},
            {'name': 'Lancement de produit', 'description': 'Événement de lancement', 'icon': 'rocket'},
            {'name': 'Retraite', 'description': 'Fête de départ à la retraite', 'icon': 'award'},
            {'name': 'Baby Shower', 'description': 'Fête prénatale', 'icon': 'baby-carriage'},
            {'name': 'Enterrement de vie', 'description': 'Enterrement de vie de jeune fille/garçon', 'icon': 'glass-cheers'},
            {'name': 'Graduation', 'description': 'Cérémonie de remise de diplôme', 'icon': 'graduation-cap'},
            {'name': 'Autre', 'description': 'Autre type d\'événement', 'icon': 'calendar'},
        ]

        created_count = 0
        for event_data in events:
            event, created = EventType.objects.get_or_create(
                name=event_data['name'],
                defaults={
                    'description': event_data['description'],
                    'icon': event_data['icon']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {event.name}'))
                created_count += 1
            else:
                self.stdout.write(f'  - {event.name} (existant)')

        self.stdout.write(self.style.SUCCESS(f'\n✅ {created_count} types d\'événements créés!'))
