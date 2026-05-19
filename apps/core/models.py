from django.db import models


class Country(models.Model):
    """Modèle pour gérer les pays disponibles sur la plateforme"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom du pays')
    code = models.CharField(max_length=2, unique=True, verbose_name='Code ISO', help_text='Code ISO 2 lettres (TG, BJ, GH...)')
    flag_emoji = models.CharField(max_length=10, blank=True, verbose_name='Drapeau emoji', help_text='Ex: 🇹🇬')
    is_active = models.BooleanField(default=True, verbose_name='Actif', db_index=True)
    display_order = models.IntegerField(default=0, verbose_name='Ordre d\'affichage')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pays'
        verbose_name_plural = 'Pays'
        ordering = ['display_order', 'name']

    def __str__(self):
        if self.flag_emoji:
            return f"{self.flag_emoji} {self.name}"
        return self.name


class TermsOfService(models.Model):
    """Conditions générales d'utilisation"""
    title = models.CharField(max_length=200, verbose_name='Titre')
    content = models.TextField(verbose_name='Contenu')
    version = models.CharField(max_length=20, verbose_name='Version', default='1.0')
    effective_date = models.DateField(verbose_name='Date d\'entrée en vigueur')
    is_active = models.BooleanField(default=True, verbose_name='Actif', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conditions générales d\'utilisation'
        verbose_name_plural = 'Conditions générales d\'utilisation'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - v{self.version}"


class City(models.Model):
    """Modèle pour gérer les villes disponibles sur la plateforme"""
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name='cities',
        verbose_name='Pays',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100, verbose_name='Nom de la ville')
    is_active = models.BooleanField(default=True, verbose_name='Actif', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ville'
        verbose_name_plural = 'Villes'
        ordering = ['country__name', 'name']
        unique_together = ['country', 'name']

    def __str__(self):
        if self.country:
            return f"{self.name} ({self.country.name})"
        return self.name


class ContactMessage(models.Model):
    """Messages de contact reçus via le formulaire"""

    SUBJECT_CHOICES = [
        ('general', 'Question générale'),
        ('vendor', 'Devenir prestataire'),
        ('technical', 'Problème technique'),
        ('partnership', 'Partenariat'),
        ('other', 'Autre'),
    ]

    STATUS_CHOICES = [
        ('new', 'Nouveau'),
        ('read', 'Lu'),
        ('replied', 'Répondu'),
        ('archived', 'Archivé'),
    ]

    name = models.CharField(max_length=100, verbose_name='Nom complet')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    subject = models.CharField(
        max_length=20,
        choices=SUBJECT_CHOICES,
        default='general',
        verbose_name='Sujet'
    )
    message = models.TextField(verbose_name='Message')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Statut'
    )
    admin_notes = models.TextField(blank=True, verbose_name='Notes admin')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Reçu le')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()} ({self.created_at.strftime('%d/%m/%Y')})"


class ErrorLog(models.Model):
    """Erreurs applicatives capturées en production"""
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    url = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    error_type = models.CharField(max_length=200, db_index=True)
    error_message = models.TextField()
    traceback = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = 'Erreur'
        verbose_name_plural = 'Erreurs'
        ordering = ['-occurred_at']

    def __str__(self):
        return f"{self.error_type} — {self.url} ({self.occurred_at:%d/%m/%Y %H:%M})"
