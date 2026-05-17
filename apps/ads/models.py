from datetime import date
from django.core.exceptions import ValidationError
from django.db import models


class Advertisement(models.Model):
    HERO = 'hero'
    BETWEEN_SECTIONS = 'between_sections'
    VENDOR_LIST_TOP = 'vendor_list_top'
    VENDOR_DETAIL = 'vendor_detail'

    ZONE_CHOICES = [
        (HERO, 'Hero homepage'),
        (BETWEEN_SECTIONS, 'Inter-sections homepage'),
        (VENDOR_LIST_TOP, 'Top liste prestataires'),
        (VENDOR_DETAIL, 'Bas fiche prestataire'),
    ]

    zone = models.CharField(max_length=30, choices=ZONE_CHOICES, db_index=True, verbose_name='Zone')
    image = models.ImageField(upload_to='ads/', verbose_name='Image')
    link_url = models.URLField(blank=True, verbose_name='Lien (optionnel)')
    alt_text = models.CharField(max_length=200, verbose_name='Texte alternatif')
    start_date = models.DateField(verbose_name='Date de début')
    end_date = models.DateField(verbose_name='Date de fin')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Publicité'
        verbose_name_plural = 'Publicités'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_zone_display()} — {self.alt_text}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': "La date de fin doit être postérieure à la date de début."})

    @property
    def status(self):
        today = date.today()
        if not self.is_active:
            return 'inactive'
        if self.start_date > today:
            return 'planned'
        if self.end_date < today:
            return 'expired'
        return 'active'

    @classmethod
    def active_for_zone(cls, zone):
        today = date.today()
        return list(cls.objects.filter(
            zone=zone,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today,
        ))
