import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from django.core import signing
from .models import VendorProfile, ContactView, VendorApplication, ServiceType
from apps.core.cache_utils import get_cached_service_types, get_cached_event_types
from apps.core.models import City, Country
from apps.core.turnstile import verify_turnstile
from .tasks import send_application_confirmation, notify_admin_new_application, send_vendor_message


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
    """Liste publique des prestataires — catégories ou résultats de recherche"""
    service_type_ids = request.GET.getlist('service_types')
    search = request.GET.get('search', '').strip()
    country_id = request.GET.get('country_id', '').strip()
    city_id = request.GET.get('city_id', '').strip()

    all_service_types = get_cached_service_types(ordered=True)

    base_context = {
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

    if search:
        from .search import semantic_search
        results = semantic_search(search, limit=20)
        return render(request, 'vendors/vendor_list.html', {
            **base_context,
            'search_results': results,
            'is_search': True,
        })

    if service_type_ids:
        active_service_types = [s for s in all_service_types if str(s.id) in service_type_ids]
    else:
        active_service_types = all_service_types

    vendors_by_category = []
    for service_type in active_service_types:
        qs = VendorProfile.objects.filter(is_active=True, service_types=service_type)
        if city_id:
            qs = qs.filter(cities__id=city_id)
        elif country_id:
            qs = qs.filter(cities__country_id=country_id)
        qs = qs.prefetch_related(
            'cities', 'service_types', 'images'
        ).order_by('-is_featured', '-created_at').distinct()[:6]
        if qs.exists():
            vendors_by_category.append({'service_type': service_type, 'vendors': qs})

    return render(request, 'vendors/vendor_list.html', {
        **base_context,
        'vendors_by_category': vendors_by_category,
        'is_search': False,
    })


def vendor_detail(request, slug):
    """Détails publics d'un prestataire"""
    vendor = get_object_or_404(
        VendorProfile.objects.prefetch_related(
            'cities', 'service_types', 'countries', 'images'
        ).select_related('source_application'),
        slug=slug,
        is_active=True
    )
    context = {
        'vendor': vendor,
        'event_types': get_cached_event_types(),
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Prestataires', 'url': 'vendors:vendor_list'},
            {'title': vendor.business_name},
        ],
    }
    return render(request, 'vendors/vendor_detail.html', context)


def vendor_detail_by_pk(request, pk):
    """Redirect legacy pk-based URLs to the slug-based URL (301 permanent)"""
    vendor = get_object_or_404(VendorProfile, pk=pk, is_active=True)
    return redirect('vendors:vendor_detail', slug=vendor.slug, permanent=True)


@require_POST
def reveal_contact(request, slug):
    """Trace le clic en base et retourne le numéro WhatsApp"""
    from django.utils import timezone
    from datetime import timedelta
    from apps.projects.models import EventType

    vendor = get_object_or_404(VendorProfile, slug=slug, is_active=True)

    whatsapp = vendor.whatsapp
    if not whatsapp:
        try:
            whatsapp = vendor.source_application.whatsapp
        except Exception:
            whatsapp = None

    if not whatsapp:
        return JsonResponse({'error': 'Aucun numéro disponible'}, status=404)

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')

    # Rate limit : 100 révélations par IP par heure
    one_hour_ago = timezone.now() - timedelta(hours=1)
    if ContactView.objects.filter(ip_address=ip, viewed_at__gte=one_hour_ago).count() >= 100:
        return JsonResponse({'error': 'Limite atteinte, réessayez dans une heure.'}, status=429)

    try:
        body = json.loads(request.body or b'{}')
    except ValueError:
        body = {}
    event_type = EventType.objects.filter(pk=body.get('event_type_id')).first()

    ContactView.objects.create(
        vendor=vendor,
        event_type=event_type,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        session_key=request.session.session_key or '',
    )

    return JsonResponse({'whatsapp': whatsapp})


def vendor_signup(request):
    """Formulaire public de candidature prestataire (étape 1 : infos + logo)"""
    service_types = ServiceType.objects.all().order_by('name')
    cities_json = _build_cities_json()
    countries_list_json = _build_countries_list_json()

    locations_json_val = '[]'

    if request.method == 'POST':
        locations_json_val = request.POST.get('locations_json', '[]')
        token = request.POST.get('cf-turnstile-response', '')
        if not verify_turnstile(token):
            messages.error(request, "Veuillez confirmer que vous n'êtes pas un robot.")
        else:
            name = request.POST.get('name', '').strip()
            business_name = request.POST.get('business_name', '').strip()
            other_service = request.POST.get('other_service', '').strip()
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
            if not service_type_ids and not other_service:
                errors.append('Veuillez sélectionner au moins un type de prestation ou préciser votre activité.')

            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                create_kwargs = dict(
                    name=name,
                    business_name=business_name,
                    other_service=other_service,
                    email=email,
                    whatsapp=whatsapp,
                    address=address,
                    description=description,
                    instagram=instagram,
                    facebook=facebook,
                )
                if 'logo' in request.FILES:
                    create_kwargs['logo'] = request.FILES['logo']
                application = VendorApplication.objects.create(**create_kwargs)
                application.service_types.set(service_type_ids)
                country_ids = [g['country_id'] for g in groups if g.get('country_id')]
                city_ids = [cid for g in groups for cid in g.get('city_ids', [])]
                application.countries.set(country_ids)
                application.cities.set(city_ids)
                if email:
                    send_application_confirmation(name, email)
                service_names = ', '.join(
                    ServiceType.objects.filter(id__in=service_type_ids).values_list('name', flat=True)
                )
                notify_admin_new_application(
                    name=name,
                    business_name=business_name,
                    service_types_str=service_names or other_service,
                    email=email,
                    whatsapp=whatsapp,
                )
                # Générer un token signé pour la page portfolio
                portfolio_token = signing.dumps(application.pk, salt='vendor-portfolio')
                return redirect('vendors:vendor_signup_portfolio', token=portfolio_token)

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


def vendor_signup_portfolio(request, token):
    """Étape 2 : upload des photos de portfolio (optionnel) après création de la candidature"""
    try:
        application_pk = signing.loads(token, salt='vendor-portfolio', max_age=3600 * 24)
        application = get_object_or_404(VendorApplication, pk=application_pk)
    except signing.BadSignature:
        return redirect('vendors:vendor_signup')

    uploaded = False
    error_msg = None

    if request.method == 'POST':
        images = request.FILES.getlist('images')
        if len(images) > 5:
            error_msg = 'Maximum 5 photos autorisées. Veuillez en sélectionner 5 ou moins.'
        else:
            for i, img in enumerate(images[:5], start=1):
                setattr(application, f'image_{i}', img)
            application.save()
            uploaded = True
            return redirect('vendors:vendor_signup_success_final', token=token)

    return render(request, 'vendors/vendor_signup_portfolio.html', {
        'application': application,
        'token': token,
        'error_msg': error_msg,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Devenir prestataire'},
        ],
    })


def vendor_signup_success_final(request, token):
    """Page de succès finale après upload portfolio (ou skip)"""
    try:
        application_pk = signing.loads(token, salt='vendor-portfolio', max_age=3600 * 24)
        application = get_object_or_404(VendorApplication, pk=application_pk)
    except signing.BadSignature:
        return redirect('vendors:vendor_signup')

    return render(request, 'vendors/vendor_signup_success.html', {
        'name': application.name,
        'has_email': bool(application.email),
        'has_whatsapp': bool(application.whatsapp),
    })


def vendor_message_reply(request, token):
    """Page publique de réponse à un message admin (lien unique)"""
    from .models import VendorMessage
    from django.utils import timezone

    message = get_object_or_404(VendorMessage, token=token)

    # Lien déjà utilisé
    if message.token_used:
        return render(request, 'vendors/vendor_message_reply.html', {
            'already_used': True,
            'message': message,
        })

    if request.method == 'POST':
        reply_body = request.POST.get('reply_body', '').strip()
        images = request.FILES.getlist('images')

        if not reply_body:
            return render(request, 'vendors/vendor_message_reply.html', {
                'message': message,
                'error_msg': 'Veuillez écrire votre réponse avant d\'envoyer.',
            })

        if len(images) > 3:
            return render(request, 'vendors/vendor_message_reply.html', {
                'message': message,
                'error_msg': 'Maximum 3 photos autorisées.',
            })

        message.reply_body = reply_body
        for i, img in enumerate(images[:3], start=1):
            setattr(message, f'reply_image_{i}', img)
        message.token_used = True
        message.status = 'replied'
        message.replied_at = timezone.now()
        message.save()

        return render(request, 'vendors/vendor_message_reply.html', {
            'replied': True,
            'message': message,
        })

    return render(request, 'vendors/vendor_message_reply.html', {
        'message': message,
    })


def vendor_pitch(request):
    """Page de présentation pour les prestataires potentiels"""
    return render(request, 'vendors/vendor_pitch.html', {
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Devenir prestataire'},
        ],
    })
