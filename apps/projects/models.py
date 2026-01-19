from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.vendors.models import ServiceType, VendorProfile


class EventType(models.Model):
    """Types d'événements"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom de l\'événement')
    description = models.TextField(blank=True, verbose_name='Description')
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Type d\'événement'
        verbose_name_plural = 'Types d\'événements'
        ordering = ['name']

    def __str__(self):
        return self.name


class Project(models.Model):
    # Accompagnement admin event
    admin_event_help = models.BooleanField(
        default=False,
        verbose_name="Accompagnement par l'admin event",
        help_text="Si coché, l'admin event est l'interlocuteur unique pour ce projet."
    )
    """Projet événementiel créé par un client"""
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name='Client'
    )
    title = models.CharField(max_length=200, verbose_name='Titre du projet')
    event_type = models.ForeignKey(
        EventType,
        on_delete=models.SET_NULL,
        null=True,
        related_name='projects',
        verbose_name='Type d\'événement'
    )
    description = models.TextField(verbose_name='Description détaillée')

    # Informations de l'événement
    event_date = models.DateField(verbose_name='Date de l\'événement')
    event_time = models.TimeField(null=True, blank=True, verbose_name='Heure de l\'événement')
    city = models.CharField(max_length=100, verbose_name='Ville')
    location = models.CharField(max_length=300, blank=True, verbose_name='Lieu précis')
    guest_count = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Nombre d\'invités estimé'
    )

    # Budget
    budget_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Budget minimum (FCFA)'
    )
    budget_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Budget maximum (FCFA)'
    )

    # Services recherchés
    services_needed = models.ManyToManyField(
        ServiceType,
        related_name='projects',
        verbose_name='Services recherchés'
    )

    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Statut',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Projet'
        verbose_name_plural = 'Projets'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.client.get_full_name()}"

    @property
    def is_active(self):
        return self.status in ['published', 'in_progress']

    @property
    def has_recommendations(self):
        """Vérifie si le projet a des recommandations Suzy"""
        return self.recommendations.exists()


class AdminRecommendation(models.Model):
    """
    Recommandations de prestataires par l'équipe Suzy (admin).
    Permet à l'admin de suggérer des prestataires adaptés au projet du client.
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),      # Recommandation créée, client pas encore notifié
        ('sent', 'Envoyée'),            # Client notifié
        ('viewed', 'Vue'),              # Client a vu la recommandation
        ('contacted', 'Contacté'),      # Client a demandé un devis au prestataire
        ('accepted', 'Acceptée'),       # Client a accepté une proposition de ce prestataire
        ('declined', 'Déclinée'),       # Client a décliné cette recommandation
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name='Projet'
    )
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='admin_recommendations',
        verbose_name='Prestataire recommandé'
    )

    # Message personnalisé de Suzy
    admin_note = models.TextField(
        verbose_name='Note de Suzy',
        help_text='Pourquoi ce prestataire est recommandé pour ce projet'
    )

    # Qui a fait la recommandation
    recommended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recommendations_made',
        verbose_name='Recommandé par'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Statut'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Envoyée le')
    viewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Vue le')

    class Meta:
        verbose_name = 'Recommandation Suzy'
        verbose_name_plural = 'Recommandations Suzy'
        ordering = ['-created_at']
        # Un prestataire ne peut être recommandé qu'une fois par projet
        unique_together = ['project', 'vendor']

    def __str__(self):
        return f"{self.vendor.business_name} → {self.project.title}"

    def mark_as_sent(self):
        """Marque la recommandation comme envoyée"""
        if self.status == 'pending':
            self.status = 'sent'
            self.sent_at = timezone.now()
            self.save(update_fields=['status', 'sent_at'])

    def mark_as_viewed(self):
        """Marque la recommandation comme vue par le client"""
        if self.status in ['pending', 'sent']:
            self.status = 'viewed'
            self.viewed_at = timezone.now()
            self.save(update_fields=['status', 'viewed_at'])

    def mark_as_contacted(self):
        """Le client a demandé un devis à ce prestataire"""
        self.status = 'contacted'
        self.save(update_fields=['status'])
