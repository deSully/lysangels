from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour LysAngels.
    Trois types d'utilisateurs : Client, Prestataire, Admin
    """
    USER_TYPE_CHOICES = [
        ('client', 'Client'),
        ('provider', 'Prestataire'),
        ('admin', 'Administrateur Susy Event'),
    ]

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='client',
        verbose_name='Type d\'utilisateur'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Téléphone'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ville'
    )
    profile_image = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        verbose_name='Photo de profil'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Compte vérifié'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"

    @property
    def is_client(self):
        return self.user_type == 'client'

    @property
    def is_provider(self):
        return self.user_type == 'provider'

    @property
    def is_susy_admin(self):
        return self.user_type == 'admin'
