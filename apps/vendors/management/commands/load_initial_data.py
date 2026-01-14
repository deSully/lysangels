from django.core.management.base import BaseCommand
from apps.vendors.models import ServiceType
from apps.projects.models import EventType


class Command(BaseCommand):
    help = 'Charge les données initiales pour LysAngels'

    def handle(self, *args, **kwargs):
        self.stdout.write('Chargement des types de services...')

        services = [
            {'name': 'Salle de réception', 'description': 'Location de salles pour événements', 'icon': 'building'},
            {'name': 'Traiteur', 'description': 'Services de restauration et buffet', 'icon': 'utensils'},
            {'name': 'Décoration', 'description': 'Décoration et aménagement d\'espace', 'icon': 'palette'},
            {'name': 'Photographe', 'description': 'Photographie professionnelle', 'icon': 'camera'},
            {'name': 'Vidéaste', 'description': 'Vidéographie et montage', 'icon': 'video'},
            {'name': 'DJ / Musique', 'description': 'Animation musicale et sonorisation', 'icon': 'music'},
            {'name': 'Animation', 'description': 'Animateurs et spectacles', 'icon': 'star'},
            {'name': 'Maquillage / Coiffure', 'description': 'Services beauté pour mariées et invités', 'icon': 'brush'},
            {'name': 'Pâtisserie', 'description': 'Gâteaux et desserts sur mesure', 'icon': 'cake'},
            {'name': 'Location matériel', 'description': 'Tables, chaises, vaisselle, etc.', 'icon': 'box'},
            {'name': 'Transport', 'description': 'Véhicules pour mariés et invités', 'icon': 'car'},
            {'name': 'Fleuriste', 'description': 'Compositions florales', 'icon': 'flower'},
        ]

        for service_data in services:
            service, created = ServiceType.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'icon': service_data['icon']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Service créé: {service.name}'))
            else:
                self.stdout.write(f'  Service existant: {service.name}')

        self.stdout.write('\nChargement des types d\'événements...')

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
            {'name': 'Autre', 'description': 'Autre type d\'événement', 'icon': 'calendar'},
        ]

        for event_data in events:
            event, created = EventType.objects.get_or_create(
                name=event_data['name'],
                defaults={
                    'description': event_data['description'],
                    'icon': event_data['icon']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Événement créé: {event.name}'))
            else:
                self.stdout.write(f'  Événement existant: {event.name}')

        self.stdout.write(self.style.SUCCESS('\n✅ Données initiales chargées avec succès!'))
