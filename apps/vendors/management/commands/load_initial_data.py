from django.core.management.base import BaseCommand
from apps.vendors.models import ServiceType
from apps.projects.models import EventType
from apps.core.models import Country, City


class Command(BaseCommand):
    help = 'Charge les données initiales pour LysAngels'

    def handle(self, *args, **kwargs):
        self.stdout.write('Chargement des types de services...')

        services = [
            # ── Groupe 1 : services de base ──
            {'name': 'Salle de réception',         'description': 'Location de salles pour événements',                     'icon': 'building'},
            {'name': 'Traiteur',                   'description': 'Services de restauration et buffet',                     'icon': 'utensils'},
            {'name': 'Décoration',                 'description': "Décoration et aménagement d'espace",                     'icon': 'palette'},
            {'name': 'Photographe',                'description': 'Photographie professionnelle',                           'icon': 'camera'},
            {'name': 'Vidéaste',                   'description': 'Vidéographie et montage',                                'icon': 'video'},
            {'name': 'DJ / Musique',               'description': 'Animation musicale et sonorisation',                     'icon': 'music'},
            {'name': 'Animation',                  'description': 'Animateurs et spectacles',                               'icon': 'star'},
            {'name': 'Maquillage / Coiffure',      'description': 'Services beauté pour mariées et invités',                'icon': 'brush'},
            {'name': 'Pâtisserie',                'description': 'Gâteaux et desserts sur mesure',                         'icon': 'cake'},
            {'name': 'Location matériel',          'description': 'Tables, chaises, vaisselle, etc.',                       'icon': 'box'},
            {'name': 'Transport',                  'description': 'Véhicules pour mariés et invités',                       'icon': 'car'},
            {'name': 'Fleuriste',                  'description': 'Compositions florales',                                  'icon': 'flower'},
            {'name': 'Communication / Marketing',  'description': 'Agences de communication et marketing événementiel',    'icon': 'megaphone'},
            # ── Groupe 2 : services spécialisés ──
            {'name': 'Tenue & Couture',            'description': 'Création et location de tenues de cérémonie',           'icon': 'shirt'},
            {'name': 'Sono & Éclairage',           'description': 'Location et installation de matériel son et lumière',   'icon': 'speaker'},
            {'name': 'Sécurité événementielle',    'description': 'Service de sécurité pour événements',                   'icon': 'shield'},
            {'name': 'Planification & Coordination','description': "Wedding planner et coordinateur d'événements",         'icon': 'clipboard'},
            {'name': 'Impression & Faire-part',    'description': 'Faire-part, menus et supports imprimés personnalisés',  'icon': 'printer'},
            {'name': 'Bijouterie & Accessoires',   'description': 'Bijoux et accessoires pour mariées et cérémonies',      'icon': 'gem'},
            {'name': 'Location mobilier',          'description': 'Location de mobilier événementiel',                     'icon': 'armchair'},
            {'name': 'Photobooth & Divertissement','description': 'Photobooth et animations interactives',                 'icon': 'camera'},
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

        self.stdout.write('\nChargement des pays d\'Afrique de l\'Ouest...')

        countries_data = [
            {'name': 'Togo',          'code': 'TG', 'flag_emoji': '🇹🇬', 'display_order': 1},
            {'name': 'Bénin',         'code': 'BJ', 'flag_emoji': '🇧🇯', 'display_order': 2},
            {'name': 'Ghana',         'code': 'GH', 'flag_emoji': '🇬🇭', 'display_order': 3},
            {'name': 'Côte d\'Ivoire','code': 'CI', 'flag_emoji': '🇨🇮', 'display_order': 4},
            {'name': 'Sénégal',       'code': 'SN', 'flag_emoji': '🇸🇳', 'display_order': 5},
            {'name': 'Nigeria',       'code': 'NG', 'flag_emoji': '🇳🇬', 'display_order': 6},
            {'name': 'Burkina Faso',  'code': 'BF', 'flag_emoji': '🇧🇫', 'display_order': 7},
            {'name': 'Mali',          'code': 'ML', 'flag_emoji': '🇲🇱', 'display_order': 8},
            {'name': 'Niger',         'code': 'NE', 'flag_emoji': '🇳🇪', 'display_order': 9},
            {'name': 'Guinée',        'code': 'GN', 'flag_emoji': '🇬🇳', 'display_order': 10},
            {'name': 'Cameroun',      'code': 'CM', 'flag_emoji': '🇨🇲', 'display_order': 11},
        ]

        country_objects = {}
        for c in countries_data:
            country, created = Country.objects.get_or_create(
                code=c['code'],
                defaults={'name': c['name'], 'flag_emoji': c['flag_emoji'], 'display_order': c['display_order']}
            )
            country_objects[c['code']] = country
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Pays créé: {c["flag_emoji"]} {country.name}'))
            else:
                self.stdout.write(f'  Pays existant: {country.name}')

        self.stdout.write('\nChargement des villes...')

        cities_data = [
            # Togo
            ('TG', 'Lomé'), ('TG', 'Kpalimé'), ('TG', 'Sokodé'),
            ('TG', 'Kara'), ('TG', 'Atakpamé'), ('TG', 'Tsévié'),
            # Bénin
            ('BJ', 'Cotonou'), ('BJ', 'Porto-Novo'), ('BJ', 'Parakou'),
            ('BJ', 'Abomey-Calavi'), ('BJ', 'Bohicon'), ('BJ', 'Natitingou'),
            # Ghana
            ('GH', 'Accra'), ('GH', 'Kumasi'), ('GH', 'Tamale'),
            ('GH', 'Cape Coast'), ('GH', 'Tema'), ('GH', 'Sekondi-Takoradi'),
            # Côte d'Ivoire
            ('CI', 'Abidjan'), ('CI', 'Yamoussoukro'), ('CI', 'Bouaké'),
            ('CI', 'Daloa'), ('CI', 'San-Pédro'), ('CI', 'Korhogo'),
            # Sénégal
            ('SN', 'Dakar'), ('SN', 'Saint-Louis'), ('SN', 'Thiès'),
            ('SN', 'Ziguinchor'), ('SN', 'Touba'), ('SN', 'Mbour'),
            # Nigeria
            ('NG', 'Lagos'), ('NG', 'Abuja'), ('NG', 'Ibadan'),
            ('NG', 'Kano'), ('NG', 'Port Harcourt'), ('NG', 'Benin City'),
            # Burkina Faso
            ('BF', 'Ouagadougou'), ('BF', 'Bobo-Dioulasso'), ('BF', 'Koudougou'),
            ('BF', 'Banfora'), ('BF', 'Ouahigouya'),
            # Mali
            ('ML', 'Bamako'), ('ML', 'Sikasso'), ('ML', 'Mopti'),
            ('ML', 'Ségou'), ('ML', 'Kayes'),
            # Niger
            ('NE', 'Niamey'), ('NE', 'Zinder'), ('NE', 'Maradi'),
            ('NE', 'Agadez'), ('NE', 'Dosso'),
            # Guinée
            ('GN', 'Conakry'), ('GN', 'Kankan'), ('GN', 'Labé'),
            ('GN', 'N\'Zérékoré'), ('GN', 'Kindia'),
            # Cameroun
            ('CM', 'Yaoundé'), ('CM', 'Douala'), ('CM', 'Garoua'),
            ('CM', 'Bamenda'), ('CM', 'Bafoussam'),
        ]

        for code, city_name in cities_data:
            country = country_objects.get(code)
            if not country:
                continue
            _, created = City.objects.get_or_create(
                country=country,
                name=city_name,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {city_name} ({code})'))

        self.stdout.write(self.style.SUCCESS('\n✅ Données initiales chargées avec succès!'))
