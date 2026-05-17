import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from .models import VendorProfile, ContactView, VendorApplication, ServiceType
from apps.core.cache_utils import get_cached_service_types
from apps.core.models import City, Country
from apps.core.turnstile import verify_turnstile
from .tasks import send_application_confirmation


def _build_cities_json():
    cities_by_country = {}
    for c in City.objects.filter(is_active=True).select_related('country').order_by('name'):
        if c.country_id:
            cities_by_country.setdefault(str(c.country_id), []).append({'id': c.id, 'name': c.name})
    return json.dumps(cities_by_country)


def _build_countries_list_json():
    return json.dumps([
        {'id': c.id, 'name': str(c)}
        for c in Country.objects.filter(is_active=True).order_by('display_order', 'name')
    ])


def vendor_list(request):
    """Liste publique des prestataires — layout catégories unique"""
    service_type_ids = request.GET.getlist('service_types')
    search = request.GET.get('search', '').strip()
    country_id = request.GET.get('country_id', '').strip()
    city_id = request.GET.get('city_id', '').strip()

    all_service_types = get_cached_service_types(ordered=True)

    if service_type_ids:
        active_service_types = [s for s in all_service_types if str(s.id) in service_type_ids]
    else:
        active_service_types = all_service_types

    vendors_by_category = []
    for service_type in active_service_types:
        qs = VendorProfile.objects.filter(is_active=True, service_types=service_type)
        if search:
            qs = qs.filter(
                Q(business_name__icontains=search) | Q(description__icontains=search)
            )
        if city_id:
            qs = qs.filter(cities__id=city_id)
        elif country_id:
            qs = qs.filter(cities__country_id=country_id)
        qs = qs.prefetch_related(
            'cities', 'service_types', 'images'
        ).order_by('-is_featured', '-created_at').distinct()[:6]
        if qs.exists():
            vendors_by_category.append({'service_type': service_type, 'vendors': qs})

    context = {
        'vendors_by_category': vendors_by_category,
        'service_types': all_service_types,
        'selected_service_types': service_type_ids,
        'search_query': search,
        'total_vendors': VendorProfile.objects.filter(is_active=True).count(),
        'countries': Country.objects.filter(is_active=True).order_by('display_order', 'name'),
        'cities_json': _build_cities_json(),
        'selected_country_id': country_id,
        'selected_city_id': city_id,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Prestataires'},
        ],
    }
    return render(request, 'vendors/vendor_list.html', context)


def vendor_detail(request, pk):
    """Détails publics d'un prestataire"""
    vendor = get_object_or_404(
        VendorProfile.objects.prefetch_related(
            'cities', 'service_types', 'countries', 'images'
        ),
        pk=pk,
        is_active=True
    )
    context = {
        'vendor': vendor,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Prestataires', 'url': 'vendors:vendor_list'},
            {'title': vendor.business_name},
        ],
    }
    return render(request, 'vendors/vendor_detail.html', context)


@require_POST
def reveal_contact(request, pk):
    """Retourne le numéro WhatsApp et trace le clic en base"""
    from django.utils import timezone
    from datetime import timedelta

    vendor = get_object_or_404(VendorProfile, pk=pk, is_active=True)

    if not vendor.whatsapp:
        return JsonResponse({'error': 'Aucun numéro disponible'}, status=404)

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')

    # Rate limit : 10 révélations par IP par heure
    one_hour_ago = timezone.now() - timedelta(hours=1)
    if ContactView.objects.filter(ip_address=ip, viewed_at__gte=one_hour_ago).count() >= 10:
        return JsonResponse({'error': 'Limite atteinte, réessayez dans une heure.'}, status=429)

    ContactView.objects.create(
        vendor=vendor,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        session_key=request.session.session_key or '',
    )

    return JsonResponse({
        'whatsapp': vendor.whatsapp,
        'whatsapp_url': f"https://wa.me/{vendor.whatsapp.replace(' ', '').replace('+', '')}",
        'vendor_name': vendor.business_name,
    })


def vendor_signup(request):
    """Formulaire public de candidature prestataire"""
    service_types = ServiceType.objects.all().order_by('name')
    cities_json = _build_cities_json()
    countries_list_json = _build_countries_list_json()

    locations_json_val = '[]'

    if request.method == 'POST':
        locations_json_val = request.POST.get('locations_json', '[]')  # lu avant le check pour le re-render
        token = request.POST.get('cf-turnstile-response', '')
        if not verify_turnstile(token):
            messages.error(request, "Veuillez confirmer que vous n'êtes pas un robot.")
        else:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            whatsapp = request.POST.get('whatsapp', '').strip()
            address = request.POST.get('address', '').strip()
            description = request.POST.get('description', '').strip()
            instagram = request.POST.get('instagram', '').strip()
            facebook = request.POST.get('facebook', '').strip()
            service_type_ids = request.POST.getlist('service_types')

            try:
                groups = json.loads(locations_json_val)
            except (ValueError, TypeError):
                groups = []

            errors = []
            if not name:
                errors.append('Le nom est requis.')
            if email and '@' not in email:
                errors.append("L'adresse email n'est pas valide.")
            if not email and not whatsapp:
                errors.append('Veuillez renseigner au moins un moyen de contact : email ou WhatsApp.')
            if not groups or not any(g.get('city_ids') for g in groups):
                errors.append('Sélectionne au moins un pays et une ville.')
            if not description:
                errors.append("La description de l'activité est requise.")
            if not service_type_ids:
                errors.append('Veuillez sélectionner au moins un type de prestation.')

            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                create_kwargs = dict(
                    name=name,
                    email=email,
                    whatsapp=whatsapp,
                    address=address,
                    description=description,
                    instagram=instagram,
                    facebook=facebook,
                )
                for i, img in enumerate(request.FILES.getlist('images')[:5], start=1):
                    create_kwargs[f'image_{i}'] = img
                application = VendorApplication.objects.create(**create_kwargs)
                application.service_types.set(service_type_ids)
                country_ids = [g['country_id'] for g in groups if g.get('country_id')]
                city_ids = [cid for g in groups for cid in g.get('city_ids', [])]
                application.countries.set(country_ids)
                application.cities.set(city_ids)
                if email:
                    send_application_confirmation(name, email)
                return render(request, 'vendors/vendor_signup_success.html', {'name': name})

    return render(request, 'vendors/vendor_signup.html', {
        'service_types': service_types,
        'cities_json': cities_json,
        'countries_list_json': countries_list_json,
        'locations_json': locations_json_val,
        'turnstile_sitekey': settings.TURNSTILE_SITEKEY,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Devenir prestataire'},
        ],
    })
