from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from apps.core.models import City, Quartier, Country
from apps.core.validators import validate_image_file  # Toujours utilisé par VendorImage


class SubscriptionTier(models.Model):
    """Types d'abonnement pour les prestataires"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Nom')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='Slug')
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Prix mensuel (FCFA)'
    )
    display_priority = models.IntegerField(
        default=0,
        verbose_name='Priorité d\'affichage',
        help_text='0 = plus haute priorité (Premium), 1 = Standard, 2 = Gratuit'
    )
    is_visible_in_list = models.BooleanField(
        default=True,
        verbose_name='Visible dans la liste par défaut',
        help_text='Si False, visible uniquement lors de recherches'
    )
    description = models.TextField(blank=True, verbose_name='Description')
    max_images = models.IntegerField(
        default=10,
        verbose_name='Nombre max d\'images',
        help_text='Nombre maximum d\'images autorisées'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Type d\'abonnement'
        verbose_name_plural = 'Types d\'abonnement'
        ordering = ['display_priority']

    def __str__(self):
        return f"{self.name} ({self.price_monthly} FCFA/mois)"


class ServiceType(models.Model):
    """Types de services proposés par les prestataires"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom du service')
    description = models.TextField(blank=True, verbose_name='Description')
    icon = models.CharField(max_length=50, blank=True, help_text='Nom de l\'icône (ex: camera, music, cake)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Type de service'
        verbose_name_plural = 'Types de services'
        ordering = ['name']

    def __str__(self):
        return self.name


class VendorProfile(models.Model):
    """Profil prestataire lié à un utilisateur"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_profile',
        verbose_name='Utilisateur'
    )
    business_name = models.CharField(max_length=200, verbose_name='Nom de l\'entreprise')
    logo = models.ImageField(
        upload_to='vendors/logos/',
        blank=True,
        null=True,
        verbose_name='Logo',
        help_text="Logo du prestataire (upload local)",
        validators=[validate_image_file]
    )
    
    # Abonnement
    subscription_tier = models.ForeignKey(
        SubscriptionTier,
        on_delete=models.PROTECT,
        related_name='vendors',
        verbose_name='Type d\'abonnement',
        null=True,
        blank=True,
        help_text='Type d\'abonnement du prestataire'
    )
    subscription_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Date d\'expiration',
        help_text='Date d\'expiration de l\'abonnement'
    )
    
    service_types = models.ManyToManyField(
        ServiceType,
        related_name='vendors',
        verbose_name='Types de services'
    )
    description = models.TextField(verbose_name='Description de l\'activité')

    # Zones d'intervention
    countries = models.ManyToManyField(
        Country,
        related_name='vendors',
        verbose_name='Pays d\'intervention',
        help_text='Pays dans lesquels le prestataire peut intervenir'
    )

    # Localisation principale
    address = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Adresse (optionnel)',
        help_text='Adresse textuelle si disponible'
    )
    google_maps_link = models.URLField(
        blank=True,
        verbose_name='Lien Google Maps',
        help_text='Collez le lien de partage de votre localisation Google Maps'
    )
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name='vendors',
        verbose_name='Ville',
        null=True,
        blank=True
    )
    quartier = models.ForeignKey(
        Quartier,
        on_delete=models.SET_NULL,
        related_name='vendors',
        verbose_name='Quartier',
        null=True,
        blank=True
    )

    website = models.URLField(blank=True, verbose_name='Site web')
    whatsapp = models.CharField(max_length=20, blank=True, verbose_name='WhatsApp')
    facebook = models.URLField(blank=True, verbose_name='Page Facebook')
    instagram = models.CharField(max_length=100, blank=True, verbose_name='Instagram')

    # Informations commerciales
    min_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Budget minimum (FCFA)'
    )
    max_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Budget maximum (FCFA)'
    )

    # Notes et avis
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name='Note moyenne',
        help_text='Note moyenne calculée automatiquement'
    )
    review_count = models.IntegerField(
        default=0,
        verbose_name='Nombre d\'avis',
        help_text='Nombre total d\'avis approuvés'
    )

    # Statut
    is_active = models.BooleanField(default=False, verbose_name='Profil actif', db_index=True)
    is_featured = models.BooleanField(default=False, verbose_name='Prestataire mis en avant', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil prestataire'
        verbose_name_plural = 'Profils prestataires'
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return self.business_name

    @property
    def is_subscription_active(self):
        """Vérifie si l'abonnement est actif"""
        if not self.subscription_tier:
            return False
        if not self.subscription_expires_at:
            return True  # Abonnement sans date d'expiration
        return timezone.now() < self.subscription_expires_at

    @property
    def is_premium(self):
        """Vérifie si le prestataire a un abonnement Premium"""
        return self.subscription_tier and self.subscription_tier.slug == 'premium'

    @property
    def subscription_status(self):
        """Retourne le statut de l'abonnement"""
        if not self.subscription_tier:
            return 'Aucun abonnement'
        if self.is_subscription_active:
            return f'{self.subscription_tier.name} - Actif'
        return f'{self.subscription_tier.name} - Expiré'
    
    def update_rating(self):
        """Recalcule la note moyenne et le nombre d'avis approuvés"""
        from django.db.models import Avg, Count
        
        approved_reviews = self.reviews.filter(status='approved')
        stats = approved_reviews.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        
        self.rating = stats['avg_rating'] or 0
        self.review_count = stats['count'] or 0
        self.save(update_fields=['rating', 'review_count'])
    
    @property
    def rating_stars(self):
        """Affichage des étoiles pour la note moyenne"""
        full_stars = int(self.rating)
        half_star = (self.rating - full_stars) >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        
        stars = '★' * full_stars
        if half_star:
            stars += '⯨'
        stars += '☆' * empty_stars
        
        return stars



class VendorImage(models.Model):
    """Images de présentation du prestataire"""
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Prestataire'
    )
    image = models.ImageField(
        upload_to='vendors/',
        verbose_name='Image',
        validators=[validate_image_file],
        help_text='Taille max: 5MB. Formats: JPEG, PNG, WebP uniquement'
    )
    caption = models.CharField(max_length=200, blank=True, verbose_name='Légende')
    is_cover = models.BooleanField(default=False, verbose_name='Image de couverture')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Image prestataire'
        verbose_name_plural = 'Images prestataires'
        ordering = ['-is_cover', '-created_at']

    def __str__(self):
        return f"Image de {self.vendor.business_name}"

    def clean(self):
        """Validation personnalisée"""
        super().clean()
        # Vérifier le nombre max d'images selon l'abonnement
        if self.vendor.subscription_tier:
            max_images = self.vendor.subscription_tier.max_images
            current_count = self.vendor.images.count()
            if not self.pk and current_count >= max_images:
                raise ValidationError(
                    f'Vous avez atteint la limite de {max_images} images pour votre abonnement {self.vendor.subscription_tier.name}.'
                )

    def save(self, *args, **kwargs):
        """Redimensionne l'image avant sauvegarde"""
        if self.image:
            self.image = self._resize_image(self.image, max_width=1200, max_height=900)
        super().save(*args, **kwargs)

    @staticmethod
    def _resize_image(image_field, max_width=1200, max_height=900):
        """Redimensionne une image en conservant les proportions"""
        try:
            img = Image.open(image_field)
            
            # Convertir en RGB si nécessaire
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Calculer les nouvelles dimensions
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Sauvegarder avec optimisation
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Créer un nouveau fichier
            return InMemoryUploadedFile(
                output,
                'ImageField',
                image_field.name,
                'image/jpeg',
                sys.getsizeof(output),
                None
            )
        except Exception as e:
            return image_field


class Review(models.Model):
    """Avis clients sur les prestataires"""
    
    MODERATION_STATUS = [
        ('pending', 'En attente de modération'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
    ]
    
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Prestataire'
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given',
        verbose_name='Client'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Projet',
        null=True,
        blank=True,
        help_text='Projet pour lequel le service a été rendu'
    )
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name='Note',
        help_text='Note de 1 à 5 étoiles'
    )
    comment = models.TextField(
        verbose_name='Commentaire',
        help_text='Votre avis détaillé sur le prestataire'
    )
    
    # Modération
    status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS,
        default='pending',
        verbose_name='Statut de modération',
        db_index=True
    )
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews_moderated',
        verbose_name='Modéré par'
    )
    moderated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Date de modération'
    )
    moderation_note = models.TextField(
        blank=True,
        verbose_name='Note de modération',
        help_text='Raison du rejet si applicable'
    )
    
    # Réponse du prestataire
    vendor_response = models.TextField(
        blank=True,
        verbose_name='Réponse du prestataire'
    )
    vendor_response_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Date de réponse'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Avis'
        verbose_name_plural = 'Avis'
        ordering = ['-created_at']
        unique_together = ['vendor', 'project']
        indexes = [
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['client', 'created_at']),
        ]

    def __str__(self):
        return f"Avis de {self.client.get_full_name()} sur {self.vendor.business_name} ({self.rating}★)"
    
    def clean(self):
        """Validation personnalisée"""
        super().clean()
        
        # Vérifier que le client n'est pas le prestataire lui-même
        if hasattr(self.client, 'vendor_profile') and self.client.vendor_profile == self.vendor:
            raise ValidationError("Vous ne pouvez pas vous auto-évaluer.")
        
        # Si un projet est spécifié, vérifier que le client en est bien le propriétaire
        if self.project and self.project.client != self.client:
            raise ValidationError("Vous ne pouvez évaluer que vos propres projets.")
    
    def approve(self, moderator):
        """Approuver l'avis"""
        self.status = 'approved'
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.save()
    
    def reject(self, moderator, reason=''):
        """Rejeter l'avis"""
        self.status = 'rejected'
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.moderation_note = reason
        self.save()
    
    def add_vendor_response(self, response):
        """Ajouter une réponse du prestataire"""
        self.vendor_response = response
        self.vendor_response_at = timezone.now()
        self.save()
    
    @property
    def is_approved(self):
        """Vérifie si l'avis est approuvé"""
        return self.status == 'approved'
    
    @property
    def stars_display(self):
        """Affichage des étoiles"""
        return '★' * self.rating + '☆' * (5 - self.rating)
