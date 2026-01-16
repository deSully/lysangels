from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta
from apps.projects.models import Project, EventType
from apps.vendors.models import ServiceType

User = get_user_model()


class ProjectCreationTests(TestCase):
    """Tests pour la création de projets"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un client
        self.client_user = User.objects.create_user(
            username='client',
            email='client@test.com',
            password='TestPass123!',
            user_type='client'
        )
        
        # Créer un type d'événement
        self.event_type = EventType.objects.create(
            name='Mariage',
            description='Cérémonies de mariage'
        )
        
        # Créer des types de services
        self.service1 = ServiceType.objects.create(name='Photographie')
        self.service2 = ServiceType.objects.create(name='Restauration')
        
        self.create_url = reverse('projects:project_create')
        
    def test_project_creation_requires_login(self):
        """Test que la création de projet nécessite une authentification"""
        response = self.client.get(self.create_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
        
    def test_create_project_success(self):
        """Test création de projet avec données valides"""
        self.client.login(username='client', password='TestPass123!')
        
        event_date = date.today() + timedelta(days=30)
        
        data = {
            'title': 'Mon Mariage',
            'event_type': self.event_type.id,
            'description': 'Un mariage magnifique',
            'event_date': event_date.isoformat(),
            'city': 'Lomé',
            'location': 'Hôtel Sarakawa',
            'guest_count': 150,
            'budget_min': 500000,
            'budget_max': 1000000,
            'services_needed': [self.service1.id, self.service2.id],
            'status': 'published'
        }
        
        response = self.client.post(self.create_url, data)
        
        # Vérifier redirection après succès
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que le projet est créé
        project = Project.objects.get(title='Mon Mariage')
        self.assertEqual(project.client, self.client_user)
        self.assertEqual(project.event_type, self.event_type)
        self.assertEqual(project.city, 'Lomé')
        self.assertEqual(project.guest_count, 150)
        self.assertEqual(project.budget_min, Decimal('500000'))
        self.assertEqual(project.services_needed.count(), 2)
        
    def test_create_project_budget_validation(self):
        """Test validation du budget (min < max)"""
        self.client.login(username='client', password='TestPass123!')
        
        event_date = date.today() + timedelta(days=30)
        
        data = {
            'title': 'Projet Test',
            'event_type': self.event_type.id,
            'description': 'Test',
            'event_date': event_date.isoformat(),
            'city': 'Lomé',
            'budget_min': 1000000,  # Plus grand que budget_max
            'budget_max': 500000,
            'services_needed': [self.service1.id],
            'status': 'draft'
        }
        
        response = self.client.post(self.create_url, data)
        
        # Devrait rester sur la page avec erreur
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.filter(title='Projet Test').exists())
        
    def test_create_project_past_date(self):
        """Test validation de la date (pas dans le passé)"""
        self.client.login(username='client', password='TestPass123!')
        
        past_date = date.today() - timedelta(days=1)
        
        data = {
            'title': 'Projet Passé',
            'event_type': self.event_type.id,
            'description': 'Test',
            'event_date': past_date.isoformat(),
            'city': 'Lomé',
            'budget_min': 100000,
            'services_needed': [self.service1.id],
            'status': 'draft'
        }
        
        response = self.client.post(self.create_url, data)
        
        # Devrait échouer
        self.assertEqual(response.status_code, 200)


class ProjectListTests(TestCase):
    """Tests pour la liste des projets"""
    
    def setUp(self):
        self.client = Client()
        
        # Créer un client
        self.client_user = User.objects.create_user(
            username='client',
            email='client@test.com',
            password='Pass123!',
            user_type='client'
        )
        
        # Créer un autre client
        self.other_client = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='Pass123!',
            user_type='client'
        )
        
        self.event_type = EventType.objects.create(name='Mariage')
        self.service = ServiceType.objects.create(name='Photo')
        
        # Créer des projets
        self.project1 = Project.objects.create(
            client=self.client_user,
            title='Mon Projet 1',
            event_type=self.event_type,
            description='Description 1',
            event_date=date.today() + timedelta(days=30),
            city='Lomé',
            budget_min=100000,
            status='published'
        )
        self.project1.services_needed.add(self.service)
        
        self.project2 = Project.objects.create(
            client=self.client_user,
            title='Mon Projet 2',
            event_type=self.event_type,
            description='Description 2',
            event_date=date.today() + timedelta(days=60),
            city='Kara',
            budget_min=200000,
            status='draft'
        )
        self.project2.services_needed.add(self.service)
        
        # Projet d'un autre client
        self.other_project = Project.objects.create(
            client=self.other_client,
            title='Autre Projet',
            event_type=self.event_type,
            description='Description autre',
            event_date=date.today() + timedelta(days=45),
            city='Lomé',
            budget_min=150000,
            status='published'
        )
        self.other_project.services_needed.add(self.service)
        
        self.list_url = reverse('projects:project_list')
        
    def test_project_list_shows_only_own_projects(self):
        """Test que la liste montre uniquement les projets de l'utilisateur connecté"""
        self.client.login(username='client', password='Pass123!')
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, 200)
        
        # Devrait contenir les 2 projets du client
        self.assertContains(response, 'Mon Projet 1')
        self.assertContains(response, 'Mon Projet 2')
        
        # Ne devrait pas contenir le projet de l'autre client
        self.assertNotContains(response, 'Autre Projet')
        
    def test_project_list_requires_login(self):
        """Test que la liste nécessite une authentification"""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)


class ProjectEditTests(TestCase):
    """Tests pour l'édition de projets"""
    
    def setUp(self):
        self.client = Client()
        
        self.client_user = User.objects.create_user(
            username='client',
            email='client@test.com',
            password='Pass123!',
            user_type='client'
        )
        
        self.other_client = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='Pass123!',
            user_type='client'
        )
        
        self.event_type = EventType.objects.create(name='Mariage')
        self.service = ServiceType.objects.create(name='Photo')
        
        self.project = Project.objects.create(
            client=self.client_user,
            title='Projet Original',
            event_type=self.event_type,
            description='Description originale',
            event_date=date.today() + timedelta(days=30),
            city='Lomé',
            budget_min=100000,
            status='draft'
        )
        self.project.services_needed.add(self.service)
        
        self.edit_url = reverse('projects:project_edit', kwargs={'pk': self.project.pk})
        
    def test_edit_project_success(self):
        """Test modification de projet avec données valides"""
        self.client.login(username='client', password='Pass123!')
        
        data = {
            'title': 'Projet Modifié',
            'event_type': self.event_type.id,
            'description': 'Description modifiée',
            'event_date': (date.today() + timedelta(days=30)).isoformat(),
            'city': 'Kara',
            'budget_min': 200000,
            'budget_max': 500000,
            'services_needed': [self.service.id]
            # Note: status n'est pas éditable via le formulaire
        }
        
        response = self.client.post(self.edit_url, data)
        
        # Vérifier redirection
        self.assertEqual(response.status_code, 302)
        
        # Vérifier modifications
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'Projet Modifié')
        self.assertEqual(self.project.city, 'Kara')
        # Le statut ne change pas car il n'est pas dans le formulaire
        self.assertEqual(self.project.status, 'draft')
        
    def test_cannot_edit_other_users_project(self):
        """Test qu'on ne peut pas modifier le projet d'un autre utilisateur"""
        self.client.login(username='other', password='Pass123!')
        
        response = self.client.get(self.edit_url)
        
        # Devrait être bloqué (403 ou redirect)
        self.assertIn(response.status_code, [302, 403, 404])


class ProjectStatusTests(TestCase):
    """Tests pour les changements de statut de projet"""
    
    def setUp(self):
        self.client = Client()
        
        self.client_user = User.objects.create_user(
            username='client',
            email='client@test.com',
            password='Pass123!',
            user_type='client'
        )
        
        self.event_type = EventType.objects.create(name='Mariage')
        self.service = ServiceType.objects.create(name='Photo')
        
        self.project = Project.objects.create(
            client=self.client_user,
            title='Projet Test',
            event_type=self.event_type,
            description='Test',
            event_date=date.today() + timedelta(days=30),
            city='Lomé',
            budget_min=100000,
            status='draft'
        )
        self.project.services_needed.add(self.service)
        
    def test_project_status_transitions(self):
        """Test les transitions de statut valides"""
        statuses = ['draft', 'published', 'in_progress', 'completed']
        
        self.client.login(username='client', password='Pass123!')
        
        for status in statuses:
            self.project.status = status
            self.project.save()
            self.project.refresh_from_db()
            self.assertEqual(self.project.status, status)
            
    def test_is_active_property(self):
        """Test la propriété is_active du projet"""
        # Draft n'est pas actif
        self.project.status = 'draft'
        self.project.save()
        self.assertFalse(self.project.is_active)
        
        # Published est actif
        self.project.status = 'published'
        self.project.save()
        self.assertTrue(self.project.is_active)
        
        # In progress est actif
        self.project.status = 'in_progress'
        self.project.save()
        self.assertTrue(self.project.is_active)
        
        # Completed n'est pas actif
        self.project.status = 'completed'
        self.project.save()
        self.assertFalse(self.project.is_active)
        
        # Cancelled n'est pas actif
        self.project.status = 'cancelled'
        self.project.save()
        self.assertFalse(self.project.is_active)

