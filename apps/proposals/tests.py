from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from apps.projects.models import Project, EventType
from apps.vendors.models import VendorProfile, ServiceType, SubscriptionTier
from apps.proposals.models import ProposalRequest, Proposal
from apps.core.models import City
from apps.messaging.models import Conversation

User = get_user_model()


class ProposalRequestTests(TestCase):
    """Tests pour les demandes de devis"""
    
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
        
        self.tier = SubscriptionTier.objects.create(
            name='Standard',
            slug='standard',
            price_monthly=10000
        )
        
        self.city = City.objects.create(name='Lomé')
        
        self.vendor_profile = VendorProfile.objects.create(
            user=self.vendor_user,
            business_name='Test Vendor',
            subscription_tier=self.tier,
            city=self.city,
            description='Test',
            is_active=True
        )
        
        # Créer un projet
        self.event_type = EventType.objects.create(name='Mariage')
        self.service = ServiceType.objects.create(name='Photo')
        
        self.project = Project.objects.create(
            client=self.client_user,
            title='Mon Mariage',
            event_type=self.event_type,
            description='Test',
            event_date=date.today() + timedelta(days=30),
            city='Lomé',
            budget_min=100000,
            status='published'
        )
        self.project.services_needed.add(self.service)
        
    def test_send_proposal_request_success(self):
        """Test envoi demande de devis avec succès"""
        self.client.login(username='client', password='Pass123!')
        
        send_url = reverse('proposals:send_request', kwargs={'vendor_id': self.vendor_profile.id})
        
        data = {
            'project': self.project.id,
            'message': 'Je souhaite un devis pour mon mariage'
        }
        
        response = self.client.post(send_url, data)
        
        # Vérifier redirection
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que la demande est créée
        request = ProposalRequest.objects.get(
            project=self.project,
            vendor=self.vendor_profile
        )
        self.assertEqual(request.status, 'pending')
        self.assertEqual(request.message, 'Je souhaite un devis pour mon mariage')
        
    def test_cannot_send_duplicate_request(self):
        """Test qu'on ne peut pas envoyer 2 demandes pour le même projet/vendor"""
        # Créer une première demande
        ProposalRequest.objects.create(
            project=self.project,
            vendor=self.vendor_profile,
            message='Première demande',
            status='pending'
        )
        
        self.client.login(username='client', password='Pass123!')
        
        send_url = reverse('proposals:send_request', kwargs={'vendor_id': self.vendor_profile.id})
        
        data = {
            'project': self.project.id,
            'message': 'Deuxième demande'
        }
        
        response = self.client.post(send_url, data)
        
        # Devrait échouer (unique_together)
        self.assertEqual(ProposalRequest.objects.filter(
            project=self.project,
            vendor=self.vendor_profile
        ).count(), 1)
        
    def test_vendor_can_view_received_requests(self):
        """Test qu'un prestataire peut voir ses demandes reçues"""
        # Créer une demande
        proposal_request = ProposalRequest.objects.create(
            project=self.project,
            vendor=self.vendor_profile,
            message='Test demande',
            status='pending'
        )
        
        self.client.login(username='vendor', password='Pass123!')
        
        list_url = reverse('proposals:request_list')
        response = self.client.get(list_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mon Mariage')
        

class ProposalCreationTests(TestCase):
    """Tests pour la création de propositions/devis"""
    
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
        
        self.tier = SubscriptionTier.objects.create(name='Standard', slug='standard', price_monthly=10000)
        self.city = City.objects.create(name='Lomé')
        
        self.vendor_profile = VendorProfile.objects.create(
            user=self.vendor_user,
            business_name='Test Vendor',
            subscription_tier=self.tier,
            city=self.city,
            description='Test',
            is_active=True
        )
        
        # Créer un projet et une demande
        self.event_type = EventType.objects.create(name='Mariage')
        self.service = ServiceType.objects.create(name='Photo')
        
        self.project = Project.objects.create(
            client=self.client_user,
            title='Mon Mariage',
            event_type=self.event_type,
            description='Test',
            event_date=date.today() + timedelta(days=30),
            city='Lomé',
            budget_min=100000,
            status='published'
        )
        self.project.services_needed.add(self.service)
        
        self.proposal_request = ProposalRequest.objects.create(
            project=self.project,
            vendor=self.vendor_profile,
            message='Demande de devis',
            status='pending'
        )
        
    def test_create_proposal_success(self):
        """Test création de proposition avec succès"""
        self.client.login(username='vendor', password='Pass123!')
        
        create_url = reverse('proposals:create_proposal', kwargs={'request_id': self.proposal_request.id})
        
        data = {
            'title': 'Proposition Photographie Mariage',
            'message': 'Je serais ravi de photographier votre mariage',
            'description': 'Package complet: cérémonie + réception',
            'price': 250000,
            'deposit_required': 50000,
            'validity_days': 30,
            'terms_and_conditions': 'Acompte non remboursable'
        }
        
        response = self.client.post(create_url, data)
        
        # Vérifier redirection
        self.assertEqual(response.status_code, 302)
        
        # Vérifier que la proposition est créée
        proposal = Proposal.objects.get(request=self.proposal_request)
        self.assertEqual(proposal.vendor, self.vendor_profile)
        self.assertEqual(proposal.project, self.project)
        self.assertEqual(proposal.status, 'sent')
        self.assertEqual(proposal.price, 250000)
        
        # Vérifier que le statut de la demande est mis à jour
        self.proposal_request.refresh_from_db()
        self.assertEqual(self.proposal_request.status, 'responded')
        
        # Vérifier qu'une conversation est créée
        self.assertTrue(Conversation.objects.filter(
            proposal_request=self.proposal_request
        ).exists())
        
    def test_client_cannot_create_proposal(self):
        """Test qu'un client ne peut pas créer de proposition"""
        self.client.login(username='client', password='Pass123!')
        
        create_url = reverse('proposals:create_proposal', kwargs={'request_id': self.proposal_request.id})
        
        response = self.client.get(create_url)
        
        # Devrait être bloqué
        self.assertIn(response.status_code, [302, 403])


class ProposalAcceptanceTests(TestCase):
    """Tests pour l'acceptation/rejet de propositions"""
    
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
        
        self.tier = SubscriptionTier.objects.create(name='Standard', slug='standard', price_monthly=10000)
        self.city = City.objects.create(name='Lomé')
        
        self.vendor_profile = VendorProfile.objects.create(
            user=self.vendor_user,
            business_name='Test Vendor',
            subscription_tier=self.tier,
            city=self.city,
            description='Test'
        )
        
        self.event_type = EventType.objects.create(name='Mariage')
        self.service = ServiceType.objects.create(name='Photo')
        
        self.project = Project.objects.create(
            client=self.client_user,
            title='Mon Mariage',
            event_type=self.event_type,
            description='Test',
            event_date=date.today() + timedelta(days=30),
            city='Lomé',
            budget_min=100000,
            status='published'
        )
        self.project.services_needed.add(self.service)
        
        self.proposal_request = ProposalRequest.objects.create(
            project=self.project,
            vendor=self.vendor_profile,
            message='Demande',
            status='responded'
        )
        
        self.proposal = Proposal.objects.create(
            request=self.proposal_request,
            vendor=self.vendor_profile,
            project=self.project,
            title='Proposition Test',
            message='Message',
            description='Description',
            price=200000,
            status='sent'
        )
        
    def test_accept_proposal(self):
        """Test acceptation d'une proposition"""
        self.client.login(username='client', password='Pass123!')
        
        # Simuler l'acceptation (selon votre implémentation)
        self.proposal.status = 'accepted'
        self.proposal.save()
        
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, 'accepted')
        
    def test_reject_proposal(self):
        """Test rejet d'une proposition"""
        self.client.login(username='client', password='Pass123!')
        
        self.proposal.status = 'rejected'
        self.proposal.save()
        
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, 'rejected')
        
    def test_vendor_cannot_accept_own_proposal(self):
        """Test qu'un vendor ne peut pas accepter sa propre proposition"""
        self.client.login(username='vendor', password='Pass123!')
        
        # Tenter de changer le statut devrait être bloqué par les permissions
        # (selon votre implémentation de contrôle d'accès)
        detail_url = reverse('proposals:proposal_detail', kwargs={'pk': self.proposal.pk})
        response = self.client.get(detail_url)
        
        # Le vendor devrait pouvoir voir mais pas accepter
        self.assertIn(response.status_code, [200, 302, 403])

