from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UserLoginTests(TestCase):
    """Tests pour l'authentification"""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')

        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='TestPass123!',
            user_type='client'
        )

    def test_login_success(self):
        """Test connexion avec identifiants valides"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_wrong_password(self):
        """Test échec connexion avec mauvais mot de passe"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_nonexistent_user(self):
        """Test échec connexion avec utilisateur inexistant"""
        response = self.client.post(self.login_url, {
            'username': 'nonexistent',
            'password': 'TestPass123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout(self):
        """Test déconnexion"""
        self.client.login(username='testuser', password='TestPass123!')
        logout_url = reverse('accounts:logout')
        response = self.client.post(logout_url)
        self.assertEqual(response.status_code, 302)


class UserModelTests(TestCase):
    """Tests pour le modèle User"""

    def test_user_type_properties(self):
        """Test les propriétés is_client, is_provider, is_admin_event"""
        client_user = User.objects.create_user(
            username='client', password='Pass123!', user_type='client'
        )
        provider_user = User.objects.create_user(
            username='provider', password='Pass123!', user_type='provider'
        )
        admin_user = User.objects.create_user(
            username='admin_user', password='Pass123!', user_type='admin'
        )

        self.assertTrue(client_user.is_client)
        self.assertFalse(client_user.is_provider)
        self.assertFalse(client_user.is_admin_event)

        self.assertFalse(provider_user.is_client)
        self.assertTrue(provider_user.is_provider)
        self.assertFalse(provider_user.is_admin_event)

        self.assertFalse(admin_user.is_client)
        self.assertFalse(admin_user.is_provider)
        self.assertTrue(admin_user.is_admin_event)

    def test_user_str(self):
        """Test la représentation string du User"""
        user = User.objects.create_user(
            username='testuser',
            first_name='Jean',
            last_name='Dupont',
            password='Pass123!',
            user_type='client'
        )
        self.assertIn('Jean Dupont', str(user))
