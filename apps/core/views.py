from django.shortcuts import render, redirect
from apps.vendors.models import VendorProfile
from apps.core.models import TermsOfService, ContactMessage
from apps.core.cache_utils import get_cached_service_types
from apps.core.forms import ContactForm
from django.contrib import messages


def home(request):
    service_types = get_cached_service_types(ordered=True)
    featured_vendors = VendorProfile.objects.filter(
        is_active=True,
        is_featured=True
    ).prefetch_related('cities', 'service_types', 'images')[:6]
    return render(request, 'core/home.html', {
        'service_types': service_types,
        'featured_vendors': featured_vendors,
    })


def about(request):
    return render(request, 'core/about.html')


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


def terms_of_service(request):
    active_terms = TermsOfService.objects.filter(is_active=True).first()
    return render(request, 'core/terms.html', {'terms': active_terms})


def privacy_policy(request):
    return render(request, 'core/privacy.html')


def legal_notice(request):
    return render(request, 'core/legal.html')
