import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import VendorProfile, ContactView, VendorApplication, ServiceType
from apps.core.cache_utils import get_cached_service_types
from apps.core.models import City, Country
from .tasks import send_application_confirmation


def _build_cities_json():
    cities_by_country = {}
    for c in City.objects.filter(is_active=True).select_related('country').order_by('name'):
        if c.country_id:
            cities_by_country.setdefault(str(c.country_id), []).append({'id': c.id, 'name': c.name})
    return json.dumps(cities_by_country)


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
            qs = qs.filter(city_id=city_id)
        elif country_id:
            qs = qs.filter(city__country_id=country_id)
        qs = qs.select_related('city').prefetch_related(
            'service_types', 'images'
        ).order_by('-is_featured', '-created_at')[:6]
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
        VendorProfile.objects.select_related('city').prefetch_related(
            'service_types', 'countries', 'images'
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
    countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
    cities_json = _build_cities_json()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        whatsapp = request.POST.get('whatsapp', '').strip()
        country_id = request.POST.get('country_id', '').strip()
        city_id = request.POST.get('city_id', '').strip()
        description = request.POST.get('description', '').strip()
        instagram = request.POST.get('instagram', '').strip()
        facebook = request.POST.get('facebook', '').strip()
        service_type_ids = request.POST.getlist('service_types')

        errors = []
        if not name:
            errors.append('Le nom est requis.')
        if not email:
            errors.append("L'email est requis.")
        if not whatsapp:
            errors.append('Le numéro WhatsApp est requis.')
        if not country_id:
            errors.append('Le pays est requis.')
        if not city_id:
            errors.append('La ville est requise.')
        if not description:
            errors.append("La description de l'activité est requise.")
        if not service_type_ids:
            errors.append('Veuillez sélectionner au moins un type de prestation.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            application = VendorApplication.objects.create(
                name=name,
                email=email,
                whatsapp=whatsapp,
                country_id=country_id,
                city_id=city_id,
                description=description,
                instagram=instagram,
                facebook=facebook,
            )
            application.service_types.set(service_type_ids)
            send_application_confirmation(name, email)
            return render(request, 'vendors/vendor_signup_success.html', {'name': name})

    return render(request, 'vendors/vendor_signup.html', {
        'service_types': service_types,
        'countries': countries,
        'cities_json': cities_json,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Devenir prestataire'},
        ],
    })
