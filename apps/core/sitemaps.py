from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.vendors.models import VendorProfile


class StaticViewsSitemap(Sitemap):
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
            'vendors:vendor_pitch',
        ]

    def location(self, item):
        return reverse(item)


class VendorSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9
    protocol = 'https'

    def items(self):
        return VendorProfile.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('vendors:vendor_detail', args=[obj.slug])
