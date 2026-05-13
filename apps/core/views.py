from django.shortcuts import render, redirect
from apps.vendors.models import ServiceType, VendorProfile
from apps.core.models import TermsOfService, ContactMessage, City
from apps.core.cache_utils import get_cached_service_types, get_cached_event_types
from apps.core.forms import ContactForm
from django.contrib import messages


def home(request):
    """Page d'accueil LysAngels — v3.0 : toutes les stats sont dynamiques"""
    service_types = get_cached_service_types(ordered=True)
    event_types = get_cached_event_types(limit=6)

    # Comptage réel depuis la base de données
    total_vendors = VendorProfile.objects.filter(is_active=True).count()
    total_service_types = ServiceType.objects.count()
    total_cities = City.objects.filter(is_active=True).count()

    featured_vendors = VendorProfile.objects.filter(
        is_active=True,
        is_featured=True
    ).prefetch_related('service_types', 'images').select_related('city')[:6]

    context = {
        'service_types': service_types,
        'event_types': event_types,
        'featured_vendors': featured_vendors,
        'stats': {
            # Données réelles — jamais de chiffres en dur
            'service_types_count': total_service_types,
            'vendors_count': total_vendors,
            'cities_count': total_cities,
        }
    }
    return render(request, 'core/home.html', context)


def about(request):
    """Page À propos — v3.0 : stats réelles + villes"""
    total_vendors = VendorProfile.objects.filter(is_active=True).count()
    total_service_types = ServiceType.objects.count()
    total_cities = City.objects.filter(is_active=True).count()
    context = {
        'stats': {
            'vendors_count': total_vendors,
            'service_types_count': total_service_types,
            'cities_count': total_cities,
        }
    }
    return render(request, 'core/about.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre message a bien été envoyé. Nous vous répondrons dans les plus brefs délais.')
            return redirect('core:contact')
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})


def how_it_works(request):
    return render(request, 'core/how_it_works.html')


def press(request):
    return render(request, 'core/press.html')


def terms_of_service(request):
    active_terms = TermsOfService.objects.filter(is_active=True).first()
    return render(request, 'core/terms.html', {'terms': active_terms})


def privacy_policy(request):
    return render(request, 'core/privacy.html')


def legal_notice(request):
    return render(request, 'core/legal.html')
