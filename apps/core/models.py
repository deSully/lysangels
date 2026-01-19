from django.db import models
from django.conf import settings


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


class UserTermsAcceptance(models.Model):
    """Acceptation des CGU par les utilisateurs"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='terms_acceptances',
        verbose_name='Utilisateur'
    )
    terms = models.ForeignKey(
        TermsOfService,
        on_delete=models.CASCADE,
        related_name='acceptances',
        verbose_name='CGU'
    )
    accepted_at = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'acceptation')
    ip_address = models.GenericIPAddressField(verbose_name='Adresse IP', null=True, blank=True)

    class Meta:
        verbose_name = 'Acceptation des CGU'
        verbose_name_plural = 'Acceptations des CGU'
        ordering = ['-accepted_at']
        unique_together = ['user', 'terms']

    def __str__(self):
        return f"{self.user.username} - {self.terms.version}"


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


class Quartier(models.Model):
    """Modèle pour gérer les quartiers par ville"""
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='quartiers', verbose_name='Ville')
    name = models.CharField(max_length=100, verbose_name='Nom du quartier')
    is_active = models.BooleanField(default=True, verbose_name='Actif', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Quartier'
        verbose_name_plural = 'Quartiers'
        ordering = ['city__name', 'name']
        unique_together = ['city', 'name']

    def __str__(self):
        return f"{self.name} ({self.city.name})"


class Notification(models.Model):
    """Notifications pour les utilisateurs"""
    
    NOTIFICATION_TYPES = [
        ('message', 'Nouveau message'),
        ('proposal', 'Nouvelle proposition'),
        ('proposal_status', 'Changement statut proposition'),
        ('request', 'Nouvelle demande de devis'),
        ('request_status', 'Changement statut demande'),
        ('recommendation', 'Recommandation Suzy'),
        ('system', 'Notification système'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Utilisateur'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name='Type'
    )
    title = models.CharField(max_length=200, verbose_name='Titre')
    message = models.TextField(verbose_name='Message')
    link = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Lien',
        help_text='URL vers la ressource concernée'
    )
    is_read = models.BooleanField(default=False, verbose_name='Lu')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Lu le')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"
    
    @classmethod
    def create_notification(cls, user, notification_type, title, message, link=''):
        """Créer une nouvelle notification"""
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link
        )
    
    @classmethod
    def mark_all_read(cls, user):
        """Marquer toutes les notifications d'un utilisateur comme lues"""
        from django.utils import timezone
        cls.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
    
    def mark_as_read(self):
        """Marquer cette notification comme lue"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


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
