from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.vendors.models import VendorProfile
from apps.projects.models import Project


class StaticViewsSitemap(Sitemap):
    """Sitemap pour les pages statiques du site"""
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            'core:home',
            'core:how_it_works',
            'core:about',
            'core:contact',
            'vendors:vendor_list',
            'accounts:register',
            'accounts:login',
        ]

    def location(self, item):
        return reverse(item)


class VendorSitemap(Sitemap):
    """Sitemap pour les profils de prestataires"""
    changefreq = 'daily'
    priority = 0.9
    protocol = 'https'

    def items(self):
        # Seulement les profils actifs
        return VendorProfile.objects.filter(
            is_active=True
        ).select_related('user')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('vendors:vendor_detail', args=[obj.pk])


class ProjectSitemap(Sitemap):
    """Sitemap pour les projets publics"""
    changefreq = 'weekly'
    priority = 0.6
    protocol = 'https'

    def items(self):
        # Seulement les projets publiés (pas les brouillons)
        return Project.objects.filter(
            status='published'
        ).select_related('client')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('projects:project_detail', args=[obj.pk])
