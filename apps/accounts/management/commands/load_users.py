"""
Commande pour charger les utilisateurs de démonstration.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

DEFAULT_PASSWORD = 'password123'


class Command(BaseCommand):
    help = 'Charge les utilisateurs de démonstration pour LysAngels'

    def handle(self, *args, **kwargs):
        self.stdout.write('Chargement des utilisateurs de démonstration...\n')

        # Administrateurs
        admins = [
            {
                'username': 'admin',
                'email': 'admin@lysangels.tg',
                'first_name': 'Super',
                'last_name': 'Admin',
                'user_type': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'admin_event',
                'email': 'admin.event@lysangels.tg',
                'first_name': 'Admin',
                'last_name': 'Event',
                'user_type': 'admin',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        # Utilisateur prestataire test
        providers = [
            {
                'username': 'provider_test',
                'email': 'provider.test@lysangels.tg',
                'first_name': 'Prestataire',
                'last_name': 'Test',
                'user_type': 'provider',
                'phone': '+228 90 00 00 01',
            },
        ]

        # Utilisateurs clients
        clients = [
            {
                'username': 'client_test',
                'email': 'client.test@lysangels.tg',
                'first_name': 'Client',
                'last_name': 'Test',
                'user_type': 'client',
                'phone': '+228 91 00 00 01',
            },
            {
                'username': 'marie_bride',
                'email': 'marie.bride@demo.lysangels.tg',
                'first_name': 'Marie',
                'last_name': 'Adjovi',
                'user_type': 'client',
                'phone': '+228 91 11 11 11',
            },
            {
                'username': 'jean_groom',
                'email': 'jean.groom@demo.lysangels.tg',
                'first_name': 'Jean',
                'last_name': 'Kossi',
                'user_type': 'client',
                'phone': '+228 91 22 22 22',
            },
            {
                'username': 'akua_birthday',
                'email': 'akua.birthday@demo.lysangels.tg',
                'first_name': 'Akua',
                'last_name': 'Mensah',
                'user_type': 'client',
                'phone': '+228 91 33 33 33',
            },
            {
                'username': 'kofi_corporate',
                'email': 'kofi.corporate@demo.lysangels.tg',
                'first_name': 'Kofi',
                'last_name': 'Amevor',
                'user_type': 'client',
                'phone': '+228 91 44 44 44',
            },
            {
                'username': 'ama_wedding',
                'email': 'ama.wedding@demo.lysangels.tg',
                'first_name': 'Ama',
                'last_name': 'Tsikata',
                'user_type': 'client',
                'phone': '+228 91 55 55 55',
            },
            {
                'username': 'yao_event',
                'email': 'yao.event@demo.lysangels.tg',
                'first_name': 'Yao',
                'last_name': 'Agbeko',
                'user_type': 'client',
                'phone': '+228 91 66 66 66',
            },
            {
                'username': 'efua_party',
                'email': 'efua.party@demo.lysangels.tg',
                'first_name': 'Efua',
                'last_name': 'Lawson',
                'user_type': 'client',
                'phone': '+228 91 77 77 77',
            },
            {
                'username': 'kwame_baptism',
                'email': 'kwame.baptism@demo.lysangels.tg',
                'first_name': 'Kwame',
                'last_name': 'Assogba',
                'user_type': 'client',
                'phone': '+228 91 88 88 88',
            },
            {
                'username': 'adjoa_gala',
                'email': 'adjoa.gala@demo.lysangels.tg',
                'first_name': 'Adjoa',
                'last_name': 'Klu',
                'user_type': 'client',
                'phone': '+228 91 99 99 99',
            },
        ]

        created_count = 0

        # Créer les admins
        self.stdout.write('\n📌 Administrateurs:')
        for user_data in admins:
            user, created = self._create_user(user_data)
            if created:
                created_count += 1

        # Créer les prestataires test
        self.stdout.write('\n📌 Prestataires:')
        for user_data in providers:
            user, created = self._create_user(user_data)
            if created:
                created_count += 1

        # Créer les clients
        self.stdout.write('\n📌 Clients:')
        for user_data in clients:
            user, created = self._create_user(user_data)
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n✅ {created_count} utilisateurs créés!'))
        self.stdout.write(f'\n🔑 Mot de passe par défaut: {DEFAULT_PASSWORD}')

    def _create_user(self, user_data):
        """Crée un utilisateur avec les données fournies."""
        username = user_data.pop('username')
        is_staff = user_data.pop('is_staff', False)
        is_superuser = user_data.pop('is_superuser', False)

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                **user_data,
                'is_verified': True,
            }
        )

        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()
            self.stdout.write(self.style.SUCCESS(f'  ✓ {username} ({user_data.get("user_type", "client")})'))
        else:
            self.stdout.write(f'  - {username} (existant)')

        return user, created
