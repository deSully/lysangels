from django.db import models
from django.conf import settings
from apps.projects.models import Project
from apps.vendors.models import VendorProfile


class ProposalRequest(models.Model):
    """Demande de devis envoyée par un client à un prestataire"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('viewed', 'Vue'),
        ('responded', 'Répondu'),
        ('declined', 'Refusée'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='proposal_requests',
        verbose_name='Projet'
    )
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='received_requests',
        verbose_name='Prestataire'
    )
    message = models.TextField(verbose_name='Message au prestataire')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Statut',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    viewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Vue le')

    class Meta:
        verbose_name = 'Demande de devis'
        verbose_name_plural = 'Demandes de devis'
        ordering = ['-created_at']
        unique_together = ['project', 'vendor']

    def __str__(self):
        return f"Demande pour {self.project.title} à {self.vendor.business_name}"


class Proposal(models.Model):
    """Proposition/Devis envoyé par un prestataire"""
    STATUS_CHOICES = [
        ('sent', 'Envoyée'),
        ('viewed', 'Vue'),
        ('accepted', 'Acceptée'),
        ('rejected', 'Refusée'),
    ]

    request = models.OneToOneField(
        ProposalRequest,
        on_delete=models.CASCADE,
        related_name='proposal',
        verbose_name='Demande'
    )
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='sent_proposals',
        verbose_name='Prestataire'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='proposals',
        verbose_name='Projet'
    )

    # Contenu de la proposition
    title = models.CharField(max_length=200, verbose_name='Titre de la proposition')
    message = models.TextField(verbose_name='Message personnalisé')
    description = models.TextField(verbose_name='Description détaillée des services')

    # Tarification
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Prix proposé (FCFA)'
    )
    deposit_required = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Acompte requis (FCFA)'
    )

    # Conditions
    terms_and_conditions = models.TextField(
        blank=True,
        verbose_name='Conditions générales'
    )
    validity_days = models.IntegerField(
        default=30,
        verbose_name='Validité (jours)'
    )

    # Fichiers joints
    attachment = models.FileField(
        upload_to='proposals/',
        blank=True,
        null=True,
        verbose_name='Fichier joint (PDF, etc.)'
    )

    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='sent',
        verbose_name='Statut',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    viewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Vue le')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='Réponse le')

    class Meta:
        verbose_name = 'Proposition'
        verbose_name_plural = 'Propositions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Proposition de {self.vendor.business_name} pour {self.project.title}"

    @property
    def client(self):
        return self.project.client
