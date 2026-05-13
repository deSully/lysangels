from django.db import models
from apps.vendors.models import ServiceType


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
    """Demande d'aide envoyée par un visiteur (sans compte)"""
    STATUS_CHOICES = [
        ('new', 'Nouvelle demande'),
        ('contacted', 'Contacté'),
        ('in_progress', 'En cours'),
        ('closed', 'Clôturé'),
    ]

    # Informations de contact
    contact_name = models.CharField(max_length=200, verbose_name='Nom complet', default='')
    contact_email = models.EmailField(verbose_name='Email', default='')
    contact_phone = models.CharField(max_length=30, blank=True, verbose_name='Téléphone')

    # Informations du projet
    title = models.CharField(max_length=200, verbose_name='Titre du projet')
    event_type = models.ForeignKey(
        EventType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        verbose_name='Type d\'événement'
    )
    description = models.TextField(verbose_name='Description détaillée')

    # Informations de l'événement
    event_date = models.DateField(null=True, blank=True, verbose_name='Date de l\'événement')
    event_time = models.TimeField(null=True, blank=True, verbose_name='Heure de l\'événement')
    city = models.CharField(max_length=100, blank=True, verbose_name='Ville')
    location = models.CharField(max_length=300, blank=True, verbose_name='Lieu précis')
    guest_count = models.IntegerField(null=True, blank=True, verbose_name='Nombre d\'invités estimé')

    # Budget
    budget_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Budget minimum (FCFA)'
    )
    budget_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Budget maximum (FCFA)'
    )

    services_needed = models.ManyToManyField(
        ServiceType,
        related_name='projects',
        verbose_name='Services recherchés',
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Statut',
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Demande client'
        verbose_name_plural = 'Demandes clients'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.contact_name}"
