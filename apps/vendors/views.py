from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import VendorProfile, ContactView
from apps.core.cache_utils import get_cached_service_types


def vendor_list(request):
    """Liste publique des prestataires — layout catégories unique"""
    service_type_ids = request.GET.getlist('service_types')
    search = request.GET.get('search', '').strip()

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
