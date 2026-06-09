from django.db import models
from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from apps.core.models import City, Country
from apps.core.validators import validate_image_file


class ServiceType(models.Model):
    """Types de services proposés par les prestataires"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom du service')
    description = models.TextField(blank=True, verbose_name='Description')
    icon = models.CharField(max_length=50, blank=True, help_text='Nom de l\'icône (ex: camera, music, cake)')
    search_keywords = models.TextField(
        blank=True,
        default='',
        verbose_name='Mots-clés de recherche',
        help_text='Mots-clés séparés par des virgules (ex: gateau, gâteau, cake, dessert)',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Type de service'
        verbose_name_plural = 'Types de services'
        ordering = ['name']

    def __str__(self):
        return self.name


class VendorProfile(models.Model):
    """Profil prestataire géré par l'équipe LysAngels"""
    business_name = models.CharField(max_length=200, verbose_name='Nom de l\'entreprise')
    logo = models.ImageField(
        upload_to='vendors/logos/',
        blank=True,
        null=True,
        verbose_name='Logo',
        validators=[validate_image_file]
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
        blank=True,
    )

    # Localisation principale
    address = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Adresse (optionnel)',
    )
    google_maps_link = models.URLField(
        blank=True,
        verbose_name='Lien Google Maps',
    )
    cities = models.ManyToManyField(
        City,
        related_name='vendor_profiles',
        verbose_name='Villes d\'intervention',
        blank=True,
    )

    email = models.EmailField(blank=True, verbose_name='Email')
    website = models.URLField(blank=True, verbose_name='Site web')
    whatsapp = models.CharField(max_length=20, blank=True, verbose_name='WhatsApp')
    facebook = models.URLField(blank=True, verbose_name='Page Facebook')
    instagram = models.CharField(max_length=100, blank=True, verbose_name='Instagram')

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

    is_active = models.BooleanField(default=False, verbose_name='Profil actif', db_index=True)
    is_featured = models.BooleanField(default=False, verbose_name='Prestataire mis en avant', db_index=True)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        verbose_name='Slug URL',
        help_text="Généré automatiquement depuis le nom de l'entreprise",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profil prestataire'
        verbose_name_plural = 'Profils prestataires'
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        if not self.slug and self.business_name:
            from django.utils.text import slugify
            base = slugify(self.business_name) or 'prestataire'
            slug = base
            n = 1
            while VendorProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


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
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            return InMemoryUploadedFile(
                output, 'ImageField', image_field.name,
                'image/jpeg', sys.getsizeof(output), None
            )
        except Exception:
            return image_field


class VendorApplication(models.Model):
    """Candidature d'un prestataire souhaitant rejoindre LysAngels"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('contacted', 'Contacté'),
        ('approved', 'Approuvé'),
        ('rejected', 'Refusé'),
    ]
    name = models.CharField(max_length=200, verbose_name='Nom complet')
    business_name = models.CharField(max_length=200, blank=True, verbose_name="Nom de l'entreprise / marque")
    email = models.EmailField(blank=True, verbose_name='Email')
    whatsapp = models.CharField(max_length=30, blank=True, verbose_name='WhatsApp')
    countries = models.ManyToManyField(
        Country,
        blank=True,
        verbose_name='Pays',
        related_name='applications',
    )
    cities = models.ManyToManyField(
        City,
        blank=True,
        verbose_name='Villes',
        related_name='applications',
    )
    service_types = models.ManyToManyField(
        ServiceType,
        related_name='applications',
        verbose_name='Types de prestation',
        blank=True,
    )
    other_service = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Autre prestation (non listée)',
        help_text='Si votre activité ne figure pas dans la liste, précisez-la ici.',
    )
    address = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Adresse / Quartier (optionnel)',
    )
    description = models.TextField(verbose_name='Description de l\'activité')
    instagram = models.CharField(max_length=200, blank=True, verbose_name='Instagram')
    facebook = models.CharField(max_length=200, blank=True, verbose_name='Facebook')
    vendor_profile = models.OneToOneField(
        'VendorProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='source_application',
        verbose_name='Profil créé',
    )
    logo = models.ImageField(
        upload_to='applications/logos/',
        blank=True,
        null=True,
        validators=[validate_image_file],
        verbose_name='Logo / photo de profil',
    )
    image_1 = models.ImageField(
        upload_to='applications/', blank=True, null=True,
        validators=[validate_image_file],
        verbose_name='Photo portfolio 1',
    )
    image_2 = models.ImageField(
        upload_to='applications/', blank=True, null=True,
        validators=[validate_image_file],
        verbose_name='Photo portfolio 2',
    )
    image_3 = models.ImageField(
        upload_to='applications/', blank=True, null=True,
        validators=[validate_image_file],
        verbose_name='Photo portfolio 3',
    )
    image_4 = models.ImageField(
        upload_to='applications/', blank=True, null=True,
        validators=[validate_image_file],
        verbose_name='Photo portfolio 4',
    )
    image_5 = models.ImageField(
        upload_to='applications/', blank=True, null=True,
        validators=[validate_image_file],
        verbose_name='Photo portfolio 5',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Statut',
        db_index=True,
    )
    admin_notes = models.TextField(blank=True, verbose_name='Notes admin')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Candidature prestataire'
        verbose_name_plural = 'Candidatures prestataires'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class VendorMessage(models.Model):
    """Message envoyé par l'admin à un prestataire (candidature), avec lien de réponse unique"""
    STATUS_CHOICES = [
        ('sent', 'Envoyé'),
        ('replied', 'Répondu'),
        ('read', 'Lu'),
        ('processed', 'Traité'),
    ]
    application = models.ForeignKey(
        'VendorApplication',
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Candidature',
        null=True,
        blank=True,
    )
    vendor_profile = models.ForeignKey(
        'VendorProfile',
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Prestataire',
        null=True,
        blank=True,
    )
    recipient_email = models.EmailField(blank=True, verbose_name='Email destinataire')
    recipient_name = models.CharField(max_length=200, blank=True, verbose_name='Nom destinataire')
    subject = models.CharField(max_length=200, verbose_name='Objet')
    body = models.TextField(verbose_name='Message')
    reply_body = models.TextField(blank=True, verbose_name='Réponse du prestataire')
    reply_image_1 = models.ImageField(
        upload_to='vendor_messages/', blank=True, null=True,
        validators=[validate_image_file], verbose_name='Photo jointe 1',
    )
    reply_image_2 = models.ImageField(
        upload_to='vendor_messages/', blank=True, null=True,
        validators=[validate_image_file], verbose_name='Photo jointe 2',
    )
    reply_image_3 = models.ImageField(
        upload_to='vendor_messages/', blank=True, null=True,
        validators=[validate_image_file], verbose_name='Photo jointe 3',
    )
    token = models.CharField(max_length=200, unique=True, verbose_name='Token de réponse')
    token_used = models.BooleanField(default=False, verbose_name='Lien utilisé')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='sent',
        verbose_name='Statut', db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    replied_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de réponse')

    class Meta:
        verbose_name = 'Message prestataire'
        verbose_name_plural = 'Messages prestataires'
        ordering = ['-created_at']

    def get_recipient_display(self):
        if self.application:
            return self.application.business_name or self.application.name
        if self.vendor_profile:
            return self.vendor_profile.business_name
        return self.recipient_name or '—'

    def __str__(self):
        return f"[{self.get_status_display()}] {self.subject} → {self.get_recipient_display()}"


class ContactView(models.Model):
    """Trace chaque fois qu'un visiteur demande à voir les coordonnées d'un prestataire"""
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='contact_views',
        verbose_name='Prestataire'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Adresse IP')
    user_agent = models.TextField(blank=True, verbose_name='User-Agent')
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name='Date du clic')
    session_key = models.CharField(max_length=40, blank=True, verbose_name='Session')

    class Meta:
        verbose_name = 'Vue coordonnées'
        verbose_name_plural = 'Vues coordonnées'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['vendor', 'viewed_at']),
        ]

    def __str__(self):
        return f"{self.vendor.business_name} — {self.viewed_at:%d/%m/%Y %H:%M} ({self.ip_address})"
