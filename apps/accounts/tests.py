from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.vendors.models import VendorProfile, SubscriptionTier
from apps.core.models import City, Quartier

User = get_user_model()


class UserRegistrationTests(TestCase):
    """Tests pour l'inscription des utilisateurs"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        
    def test_register_client_success(self):
        """Test inscription client avec données valides"""
        data = {
            'username': 'testclient',
            'email': 'client@test.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'user_type': 'client',
            'phone': '0690123456',  # 10 chiffres
            'city': 'Abidjan',
            'accept_terms': True
        }
        response = self.client.post(self.register_url, data)
        
        # Déboguer en cas d'échec
        if response.status_code != 302:
            from django.forms import forms
            if hasattr(response, 'context') and 'form' in response.context:
                print("Form errors:", response.context['form'].errors)
        
        # Vérifier redirection après succès
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que l'utilisateur est créé
        user = User.objects.get(username='testclient')
        self.assertEqual(user.email, 'client@test.com')
        self.assertEqual(user.user_type, 'client')
        self.assertTrue(user.check_password('TestPass123!'))
        
    def test_register_vendor_success(self):
        """Test inscription prestataire avec données valides"""
        data = {
            'username': 'testvendor',
            'email': 'vendor@test.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'Marie',
            'last_name': 'Martin',
            'user_type': 'provider',
            'phone': '0690654321',  # 10 chiffres
            'city': 'Abidjan',
            'accept_terms': True
        }
        response = self.client.post(self.register_url, data)
        
        # Déboguer
        if response.status_code != 302:
            if hasattr(response, 'context') and 'form' in response.context:
                print("Form errors:", response.context['form'].errors)
            # Vérifier si une exception s'est produite
            from django.contrib import messages as django_messages
            storage = django_messages.get_messages(response.wsgi_request)
            for message in storage:
                print(f"Message: {message}")
        
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(username='testvendor')
        self.assertEqual(user.user_type, 'provider')
        
        # Vérifier que le profil vendor est créé automatiquement
        self.assertTrue(hasattr(user, 'vendor_profile'))
        
    def test_register_password_mismatch(self):
        """Test échec inscription avec mots de passe différents"""
        data = {
            'username': 'testuser',
            'email': 'test@test.com',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'client',
            'phone': '90000000'
        }
        response = self.client.post(self.register_url, data)
        
        # Devrait rester sur la page avec erreurs
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testuser').exists())
        
    def test_register_duplicate_username(self):
        """Test échec inscription avec username existant"""
        # Créer un utilisateur
        User.objects.create_user(
            username='existing',
            email='existing@test.com',
            password='Pass123!'
        )
        
        # Tenter de créer un autre avec le même username
        data = {
            'username': 'existing',
            'email': 'new@test.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'user_type': 'client',
            'phone': '90111111'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='existing').count(), 1)


class UserLoginTests(TestCase):
    """Tests pour l'authentification"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.dashboard_url = reverse('accounts:dashboard')
        
        # Créer un utilisateur de test
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
        
        # Devrait rediriger vers dashboard
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que l'utilisateur est authentifié
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
    def test_login_wrong_password(self):
        """Test échec connexion avec mauvais mot de passe"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword123!'
        })
        
        # Devrait rester sur la page de login
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
        # Se connecter d'abord
        self.client.login(username='testuser', password='TestPass123!')
        
        # Se déconnecter
        logout_url = reverse('accounts:logout')
        response = self.client.post(logout_url)
        
        # Devrait rediriger
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que l'utilisateur n'est plus authentifié
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)  # Redirige vers login


class UserProfileTests(TestCase):
    """Tests pour la gestion du profil utilisateur"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='TestPass123!',
            user_type='client',
            first_name='Jean',
            last_name='Dupont'
        )
        self.profile_url = reverse('accounts:profile')
        
    def test_profile_requires_login(self):
        """Test que le profil nécessite une authentification"""
        response = self.client.get(self.profile_url)
        
        # Devrait rediriger vers login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
        
    def test_profile_accessible_when_logged_in(self):
        """Test accès profil pour utilisateur connecté"""
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jean')
        self.assertContains(response, 'Dupont')
        
    def test_profile_update(self):
        """Test mise à jour du profil"""
        self.client.login(username='testuser', password='TestPass123!')
        
        response = self.client.post(self.profile_url, {
            'first_name': 'Marie',
            'last_name': 'Martin',
            'email': 'new@test.com',
            'phone': '0698765432',  # 10 chiffres
            'city': 'Lomé'  # Ajouter city
        })
        
        # Recharger l'utilisateur
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.first_name, 'Marie')
        self.assertEqual(self.user.last_name, 'Martin')
        self.assertEqual(self.user.email, 'new@test.com')


class VendorDashboardTests(TestCase):
    """Tests pour le dashboard prestataire"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un tier gratuit
        self.free_tier = SubscriptionTier.objects.create(
            name='Gratuit',
            slug='gratuit',
            price_monthly=0,
            display_priority=2
        )
        
        # Créer une ville et quartier
        self.city = City.objects.create(name='Lomé', is_active=True)
        self.quartier = Quartier.objects.create(
            city=self.city,
            name='Nyékonakpoè',
            is_active=True
        )
        
        # Créer un prestataire
        self.vendor_user = User.objects.create_user(
            username='vendor',
            email='vendor@test.com',
            password='TestPass123!',
            user_type='provider'
        )
        
        self.vendor_profile = VendorProfile.objects.create(
            user=self.vendor_user,
            business_name='Test Vendor',
            subscription_tier=self.free_tier,
            city=self.city,
            quartier=self.quartier,
            description='Test description'
        )
        
        self.vendor_dashboard_url = reverse('vendors:dashboard')
        
    def test_vendor_dashboard_requires_login(self):
        """Test que le dashboard vendor nécessite authentification"""
        response = self.client.get(self.vendor_dashboard_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
        
    def test_vendor_dashboard_accessible(self):
        """Test accès dashboard pour prestataire connecté"""
        self.client.login(username='vendor', password='TestPass123!')
        response = self.client.get(self.vendor_dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Vendor')
        
    def test_client_cannot_access_vendor_dashboard(self):
        """Test qu'un client ne peut pas accéder au dashboard vendor"""
        client_user = User.objects.create_user(
            username='client',
            email='client@test.com',
            password='TestPass123!',
            user_type='client'
        )
        
        self.client.login(username='client', password='TestPass123!')
        response = self.client.get(self.vendor_dashboard_url)
        
        # Devrait rediriger ou renvoyer 403
        self.assertNotEqual(response.status_code, 200)


class PermissionTests(TestCase):
    """Tests pour les permissions et contrôles d'accès"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un client
        self.client_user = User.objects.create_user(
            username='client',
            email='client@test.com',
            password='Pass123!',
            user_type='client'
        )
        
        # Créer un prestataire
        self.vendor_user = User.objects.create_user(
            username='vendor',
            email='vendor@test.com',
            password='Pass123!',
            user_type='provider'
        )
        
        self.free_tier = SubscriptionTier.objects.create(
            name='Gratuit',
            slug='gratuit',
            price_monthly=0
        )
        
        self.city = City.objects.create(name='Lomé')
        
        self.vendor_profile = VendorProfile.objects.create(
            user=self.vendor_user,
            business_name='Test Vendor',
            subscription_tier=self.free_tier,
            city=self.city,
            description='Test'
        )
        
    def test_vendor_cannot_create_project(self):
        """Test qu'un prestataire ne peut pas créer de projet"""
        self.client.login(username='vendor', password='Pass123!')
        
        project_create_url = reverse('projects:project_create')
        response = self.client.get(project_create_url)
        
        # Devrait être bloqué
        self.assertIn(response.status_code, [302, 403])
        
    def test_client_cannot_edit_vendor_profile(self):
        """Test qu'un client ne peut pas éditer un profil vendor"""
        self.client.login(username='client', password='Pass123!')
        
        vendor_edit_url = reverse('vendors:profile_edit')
        response = self.client.get(vendor_edit_url)
        
        # Devrait être bloqué
        self.assertIn(response.status_code, [302, 403])

