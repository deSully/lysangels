from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import VendorProfile, ContactView
from apps.core.models import City, Country
from apps.core.cache_utils import get_cached_service_types


def vendor_list(request):
    """Liste publique des prestataires avec filtres"""
    service_type_ids = request.GET.getlist('service_types')
    city_ids = request.GET.getlist('cities')
    search = request.GET.get('search')
    has_filters = bool(search or service_type_ids or city_ids)

    total_vendors = VendorProfile.objects.filter(is_active=True).count()

    if not has_filters:
        service_types = get_cached_service_types(ordered=True)
        vendors_by_category = []
        for service_type in service_types:
            vendors = VendorProfile.objects.filter(
                is_active=True,
                service_types=service_type
            ).select_related('city').prefetch_related(
                'service_types', 'images'
            ).order_by('-is_featured', '-created_at')[:6]
            if vendors.exists():
                vendors_by_category.append({
                    'service_type': service_type,
                    'vendors': vendors
                })

        all_service_types = get_cached_service_types(ordered=True)
        all_countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
        all_cities = City.objects.filter(is_active=True).order_by('name')
        vendors_featured = VendorProfile.objects.filter(
            is_active=True,
            is_featured=True
        ).prefetch_related('service_types', 'images').select_related('city')[:6]

        context = {
            'vendors_by_category': vendors_by_category,
            'vendors_featured': vendors_featured,
            'service_types': all_service_types,
            'countries': all_countries,
            'cities': all_cities,
            'selected_service_types': [],
            'selected_cities': [],
            'search_query': search,
            'display_mode': 'categories',
            'total_vendors': total_vendors,
            'breadcrumbs': [
                {'title': 'Accueil', 'url': 'core:home'},
                {'title': 'Prestataires'},
            ],
        }
        return render(request, 'vendors/vendor_list.html', context)

    vendors = VendorProfile.objects.filter(is_active=True)
    if service_type_ids:
        vendors = vendors.filter(service_types__id__in=service_type_ids).distinct()
    if city_ids:
        vendors = vendors.filter(city__id__in=city_ids)
    if search:
        vendors = vendors.filter(
            Q(business_name__icontains=search) | Q(description__icontains=search)
        )
    vendors = vendors.select_related('city').prefetch_related(
        'service_types', 'images'
    ).order_by('-is_featured', '-created_at')

    paginator = Paginator(vendors, 12)
    try:
        page_number = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page_number = 1
    vendors_page = paginator.get_page(page_number)

    all_service_types = get_cached_service_types(ordered=True)
    all_countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
    all_cities = City.objects.filter(is_active=True).order_by('name')
    context = {
        'vendors': vendors_page,
        'service_types': all_service_types,
        'countries': all_countries,
        'cities': all_cities,
        'selected_service_types': service_type_ids,
        'selected_cities': city_ids,
        'search_query': search,
        'display_mode': 'list',
        'total_vendors': total_vendors,
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
    vendor = get_object_or_404(VendorProfile, pk=pk, is_active=True)

    if not vendor.whatsapp:
        return JsonResponse({'error': 'Aucun numéro disponible'}, status=404)

    # Récupérer l'IP réelle (derrière proxy/Nginx)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    # Logger le clic
    ContactView.objects.create(
        vendor=vendor,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        session_key=request.session.session_key or '',
    )

    return JsonResponse({
        'whatsapp': vendor.whatsapp,
        'whatsapp_url': f"https://wa.me/{vendor.whatsapp.replace(' ', '').replace('+', '')}",
    })
