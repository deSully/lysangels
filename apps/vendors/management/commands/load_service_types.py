from django.core.management.base import BaseCommand
from apps.vendors.models import ServiceType


class Command(BaseCommand):
    help = 'Charge les types de services pour LysAngels'

    def handle(self, *args, **kwargs):
        self.stdout.write('Chargement des types de services...\n')

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

        created_count = 0
        for service_data in services:
            service, created = ServiceType.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'icon': service_data['icon']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {service.name}'))
                created_count += 1
            else:
                self.stdout.write(f'  - {service.name} (existant)')

        self.stdout.write(self.style.SUCCESS(f'\n✅ {created_count} types de services créés!'))
