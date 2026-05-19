"""
Vues d'administration pour LysAngels
"""
import json
from datetime import timedelta
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from apps.core.models import City, Country, ContactMessage
from apps.vendors.models import ServiceType, VendorProfile, VendorImage, VendorApplication, ContactView
from apps.projects.models import EventType, Project, ProjectNote
from apps.ads.models import Advertisement


def _admin_build_cities_json():
    from apps.core.models import City
    cities_by_country = {}
    for c in City.objects.filter(is_active=True).select_related('country').order_by('name'):
        if c.country_id:
            cities_by_country.setdefault(str(c.country_id), []).append({'id': c.id, 'name': c.name})
    return json.dumps(cities_by_country)


def _admin_build_countries_list_json():
    from apps.core.models import Country
    return json.dumps([
        {'id': c.id, 'name': str(c)}
        for c in Country.objects.filter(is_active=True).order_by('display_order', 'name')
    ])


def admin_required(view_func):
    """Décorateur pour les vues admin."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not hasattr(request.user, 'user_type') or request.user.user_type != 'admin':
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Accès réservé à l'administrateur.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@admin_required
def admin_dashboard(request):
    """Dashboard administrateur — statistiques et graphiques analytiques."""
    from datetime import timedelta, datetime
    from django.utils import timezone
    from django.db.models.functions import TruncMonth, TruncWeek, TruncDate
    from django.db.models import Q

    now = timezone.now()

    # --- Période ---
    date_from_str = request.GET.get('date_from', '')
    date_to_str = request.GET.get('date_to', '')
    custom_period = False
    period_days = 365

    if date_from_str and date_to_str:
        try:
            date_from_dt = timezone.make_aware(datetime.strptime(date_from_str, '%Y-%m-%d'))
            date_to_dt = timezone.make_aware(
                datetime.strptime(date_to_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            )
            if date_from_dt <= date_to_dt:
                period_start = date_from_dt
                period_end = date_to_dt
                period_days = max((date_to_dt.date() - date_from_dt.date()).days + 1, 1)
                custom_period = True
        except (ValueError, TypeError):
            pass

    if not custom_period:
        try:
            period_days = int(request.GET.get('period', 365))
        except (ValueError, TypeError):
            period_days = 365
        if period_days not in (7, 30, 90, 365):
            period_days = 365
        period_start = now - timedelta(days=period_days)
        period_end = now

    period_duration = period_end - period_start
    prev_start = period_start - period_duration
    prev_end = period_start

    # KPI 1 : Nouvelles demandes en attente
    kpi_new_requests = Project.objects.filter(status='new').count()

    # KPI 2 : Demandes reçues sur la période (avec delta)
    total_period = Project.objects.filter(
        created_at__gte=period_start, created_at__lte=period_end
    ).count()
    kpi_received = total_period
    kpi_received_prev = Project.objects.filter(
        created_at__gte=prev_start, created_at__lt=prev_end
    ).count()
    kpi_received_delta = kpi_received - kpi_received_prev

    # KPI 3 : Prestataires actifs
    kpi_active_vendors = VendorProfile.objects.filter(is_active=True).count()

    # KPI 4 : Taux de traitement
    closed_period = Project.objects.filter(
        created_at__gte=period_start, created_at__lte=period_end, status='closed'
    ).count()
    kpi_rate = round(closed_period / total_period * 100) if total_period > 0 else 0

    total_prev = Project.objects.filter(
        created_at__gte=prev_start, created_at__lt=prev_end
    ).count()
    closed_prev = Project.objects.filter(
        created_at__gte=prev_start, created_at__lt=prev_end, status='closed'
    ).count()
    kpi_rate_prev = round(closed_prev / total_prev * 100) if total_prev > 0 else 0
    kpi_rate_delta = kpi_rate - kpi_rate_prev

    # Courbe de tendance (granularité adaptée à la période)
    base_qs = Project.objects.filter(created_at__gte=period_start, created_at__lte=period_end)

    if period_days <= 30:
        trend_qs = (
            base_qs.annotate(bucket=TruncDate('created_at'))
            .values('bucket').annotate(count=Count('id')).order_by('bucket')
        )
        bucket_dict = {item['bucket'].strftime('%Y-%m-%d'): item['count'] for item in trend_qs}
        trend_labels, trend_values = [], []
        cur = period_start.date()
        end_d = period_end.date()
        while cur <= end_d:
            trend_labels.append(cur.strftime('%d/%m'))
            trend_values.append(bucket_dict.get(cur.strftime('%Y-%m-%d'), 0))
            cur += timedelta(days=1)

    elif period_days <= 180:
        trend_qs = (
            base_qs.annotate(bucket=TruncWeek('created_at'))
            .values('bucket').annotate(count=Count('id')).order_by('bucket')
        )
        bucket_dict = {item['bucket'].strftime('%Y-%m-%d'): item['count'] for item in trend_qs}
        trend_labels, trend_values = [], []
        cur = period_start.date()
        cur -= timedelta(days=cur.weekday())  # lundi de la semaine
        end_d = period_end.date()
        while cur <= end_d:
            trend_labels.append(cur.strftime('%d/%m'))
            trend_values.append(bucket_dict.get(cur.strftime('%Y-%m-%d'), 0))
            cur += timedelta(weeks=1)

    else:
        trend_qs = (
            base_qs.annotate(month=TruncMonth('created_at'))
            .values('month').annotate(count=Count('id')).order_by('month')
        )
        monthly_dict = {item['month'].strftime('%Y-%m'): item['count'] for item in trend_qs}
        FR_MONTHS = ['jan.', 'fév.', 'mar.', 'avr.', 'mai', 'juin',
                     'juil.', 'août', 'sep.', 'oct.', 'nov.', 'déc.']
        trend_labels, trend_values = [], []
        cur = period_start.date().replace(day=1)
        end_month = period_end.date().replace(day=1)
        while cur <= end_month:
            key = cur.strftime('%Y-%m')
            trend_labels.append(FR_MONTHS[cur.month - 1] + ' ' + str(cur.year))
            trend_values.append(monthly_dict.get(key, 0))
            m, y = cur.month + 1, cur.year
            if m > 12:
                m, y = 1, y + 1
            cur = cur.replace(year=y, month=m)

    chart_trends = {'labels': trend_labels, 'values': trend_values}

    # Services demandés vs couverts (toute la vie de la plateforme)
    service_stats_qs = list(
        ServiceType.objects
        .annotate(
            demanded=Count('projects', distinct=True),
            covered=Count('vendors', filter=Q(vendors__is_active=True), distinct=True),
        )
        .values('name', 'demanded', 'covered')
        .order_by('-demanded')
    )
    chart_services = {
        'labels': [s['name'] for s in service_stats_qs],
        'demanded': [s['demanded'] for s in service_stats_qs],
        'covered': [s['covered'] for s in service_stats_qs],
    }

    # Types d'événements (période)
    events_qs = (
        Project.objects
        .filter(created_at__gte=period_start, created_at__lte=period_end, event_type__isnull=False)
        .values('event_type__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    chart_events = {
        'labels': [e['event_type__name'] for e in events_qs],
        'values': [e['count'] for e in events_qs],
    }

    # Pipeline CSS
    status_map = [
        ('new', 'Nouvelle demande', 'var(--terra)'),
        ('contacted', 'Contacté', '#3B82F6'),
        ('in_progress', 'En cours', '#16A34A'),
        ('closed', 'Clôturé', 'var(--muted)'),
    ]
    pipeline_display = []
    for status, label, color in status_map:
        count = Project.objects.filter(
            created_at__gte=period_start, created_at__lte=period_end, status=status
        ).count()
        pct = round(count / total_period * 100) if total_period > 0 else 0
        pipeline_display.append({'label': label, 'count': count, 'pct': pct, 'color': color})

    # Top 5 villes (période)
    cities_qs = (
        Project.objects
        .filter(created_at__gte=period_start, created_at__lte=period_end, city__isnull=False)
        .values('city__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    chart_cities = {
        'labels': [c['city__name'] for c in cities_qs],
        'values': [c['count'] for c in cities_qs],
    }

    # Aperçu opérationnel
    recent_projects = Project.objects.filter(status='new').order_by('-created_at')[:10]
    seven_days_ago = timezone.now() - timedelta(days=7)
    top_contacted_vendors = (
        VendorProfile.objects
        .filter(is_active=True)
        .annotate(views_7d=Count('contact_views', filter=Q(contact_views__viewed_at__gte=seven_days_ago)))
        .filter(views_7d__gt=0)
        .order_by('-views_7d')[:5]
    )

    context = {
        'periods': [(7, '7 jours'), (30, '30 jours'), (90, '90 jours'), (365, '12 mois')],
        'period_days': None if custom_period else period_days,
        'custom_period': custom_period,
        'date_from': date_from_str,
        'date_to': date_to_str,
        'kpi_new_requests': kpi_new_requests,
        'kpi_received': kpi_received,
        'kpi_received_delta': kpi_received_delta,
        'kpi_active_vendors': kpi_active_vendors,
        'kpi_rate': kpi_rate,
        'kpi_rate_delta': kpi_rate_delta,
        'chart_trends': chart_trends,
        'chart_services': chart_services,
        'chart_events': chart_events,
        'chart_cities': chart_cities,
        'pipeline_display': pipeline_display,
        'recent_projects': recent_projects,
        'top_contacted_vendors': top_contacted_vendors,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


# ========== GESTION DES PAYS ==========

@admin_required
def country_list(request):
    countries = Country.objects.annotate(city_count=Count('cities')).order_by('display_order', 'name')
    return render(request, 'accounts/admin/country_list.html', {'countries': countries})


@admin_required
def country_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        flag_emoji = request.POST.get('flag_emoji')
        display_order = request.POST.get('display_order', 999)
        is_active = request.POST.get('is_active') == 'on'
        if Country.objects.filter(code__iexact=code).exists():
            messages.error(request, f'Un pays avec le code "{code}" existe déjà.')
        else:
            Country.objects.create(
                name=name, code=code.upper(), flag_emoji=flag_emoji,
                display_order=display_order, is_active=is_active
            )
            messages.success(request, f'Pays "{name}" créé avec succès!')
            return redirect('accounts:admin_country_list')
    return render(request, 'accounts/admin/country_form.html')


@admin_required
def country_edit(request, pk):
    country = get_object_or_404(Country, pk=pk)
    if request.method == 'POST':
        country.name = request.POST.get('name')
        country.code = request.POST.get('code').upper()
        country.flag_emoji = request.POST.get('flag_emoji')
        country.display_order = request.POST.get('display_order', 999)
        country.is_active = request.POST.get('is_active') == 'on'
        country.save()
        messages.success(request, 'Pays modifié avec succès!')
        return redirect('accounts:admin_country_list')
    return render(request, 'accounts/admin/country_form.html', {'country': country})


@admin_required
def country_delete(request, pk):
    country = get_object_or_404(Country, pk=pk)
    if request.method == 'POST':
        try:
            country.delete()
            messages.success(request, 'Pays supprimé avec succès!')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer ce pays: {str(e)}')
        return redirect('accounts:admin_country_list')
    return render(request, 'accounts/admin/country_confirm_delete.html', {'country': country})


# ========== GESTION DES VILLES ==========

@admin_required
def city_list(request):
    cities = City.objects.annotate(vendor_count=Count('vendors')).order_by('name')
    return render(request, 'accounts/admin/city_list.html', {'cities': cities})


@admin_required
def city_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        country_id = request.POST.get('country')
        is_active = request.POST.get('is_active') == 'on'
        if not country_id:
            messages.error(request, 'Le pays est obligatoire.')
        else:
            country = get_object_or_404(Country, pk=country_id)
            City.objects.create(name=name, country=country, is_active=is_active)
            messages.success(request, f'Ville "{name}" créée avec succès!')
            return redirect('accounts:admin_city_list')
    countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
    return render(request, 'accounts/admin/city_form.html', {'countries': countries})


@admin_required
def city_edit(request, pk):
    city = get_object_or_404(City, pk=pk)
    if request.method == 'POST':
        city.name = request.POST.get('name')
        city.country_id = request.POST.get('country')
        city.is_active = request.POST.get('is_active') == 'on'
        city.save()
        messages.success(request, 'Ville modifiée avec succès!')
        return redirect('accounts:admin_city_list')
    countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
    return render(request, 'accounts/admin/city_form.html', {'city': city, 'countries': countries})


@admin_required
def city_delete(request, pk):
    city = get_object_or_404(City, pk=pk)
    if request.method == 'POST':
        try:
            city.delete()
            messages.success(request, 'Ville supprimée avec succès!')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer cette ville: {str(e)}')
        return redirect('accounts:admin_city_list')
    return render(request, 'accounts/admin/city_confirm_delete.html', {'city': city})


# ========== GESTION DES TYPES DE SERVICES ==========

@admin_required
def service_type_list(request):
    service_types = ServiceType.objects.annotate(vendor_count=Count('vendors')).order_by('name')
    return render(request, 'accounts/admin/service_type_list.html', {'service_types': service_types})


@admin_required
def service_type_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', '')
        search_keywords = request.POST.get('search_keywords', '')
        ServiceType.objects.create(name=name, description=description, icon=icon, search_keywords=search_keywords)
        messages.success(request, f'Type de service "{name}" créé avec succès!')
        return redirect('accounts:admin_service_type_list')
    return render(request, 'accounts/admin/service_type_form.html')


@admin_required
def service_type_edit(request, pk):
    service_type = get_object_or_404(ServiceType, pk=pk)
    if request.method == 'POST':
        service_type.name = request.POST.get('name')
        service_type.description = request.POST.get('description', '')
        service_type.icon = request.POST.get('icon', '')
        service_type.search_keywords = request.POST.get('search_keywords', '')
        service_type.save()
        messages.success(request, 'Type de service modifié avec succès!')
        return redirect('accounts:admin_service_type_list')
    return render(request, 'accounts/admin/service_type_form.html', {'service_type': service_type})


@admin_required
def service_type_delete(request, pk):
    service_type = get_object_or_404(ServiceType, pk=pk)
    if request.method == 'POST':
        try:
            service_type.delete()
            messages.success(request, 'Type de service supprimé avec succès!')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer: {str(e)}')
        return redirect('accounts:admin_service_type_list')
    return render(request, 'accounts/admin/service_type_confirm_delete.html', {'service_type': service_type})


# ========== GESTION DES TYPES D'ÉVÉNEMENTS ==========

@admin_required
def event_type_list(request):
    event_types = EventType.objects.annotate(project_count=Count('projects')).order_by('name')
    return render(request, 'accounts/admin/event_type_list.html', {'event_types': event_types})


@admin_required
def event_type_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', '')
        EventType.objects.create(name=name, description=description, icon=icon)
        messages.success(request, f'Type d\'événement "{name}" créé avec succès!')
        return redirect('accounts:admin_event_type_list')
    return render(request, 'accounts/admin/event_type_form.html')


@admin_required
def event_type_edit(request, pk):
    event_type = get_object_or_404(EventType, pk=pk)
    if request.method == 'POST':
        event_type.name = request.POST.get('name')
        event_type.description = request.POST.get('description', '')
        event_type.icon = request.POST.get('icon', '')
        event_type.save()
        messages.success(request, 'Type d\'événement modifié avec succès!')
        return redirect('accounts:admin_event_type_list')
    return render(request, 'accounts/admin/event_type_form.html', {'event_type': event_type})


@admin_required
def event_type_delete(request, pk):
    event_type = get_object_or_404(EventType, pk=pk)
    if request.method == 'POST':
        try:
            event_type.delete()
            messages.success(request, 'Type d\'événement supprimé avec succès!')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer: {str(e)}')
        return redirect('accounts:admin_event_type_list')
    return render(request, 'accounts/admin/event_type_confirm_delete.html', {'event_type': event_type})


# ========== GESTION DES DEMANDES CLIENTS ==========

@admin_required
def project_list(request):
    """Liste des demandes clients"""
    projects = Project.objects.select_related('event_type').order_by('-created_at')
    status = request.GET.get('status')
    if status:
        projects = projects.filter(status=status)
    paginator = Paginator(projects, 20)
    projects = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/admin/project_list.html', {
        'projects': projects,
        'selected_status': status,
        'status_choices': Project.STATUS_CHOICES,
    })


@admin_required
def project_detail(request, pk):
    """Détails d'une demande client"""
    project = get_object_or_404(Project.objects.select_related('event_type'), pk=pk)
    notes = ProjectNote.objects.filter(project=project).select_related('created_by').order_by('-created_at')
    return render(request, 'accounts/admin/project_detail.html', {
        'project': project,
        'notes': notes,
    })


@admin_required
def project_update_status(request, pk):
    """Mettre à jour le statut d'une demande"""
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = [s[0] for s in Project.STATUS_CHOICES]
        if new_status in valid_statuses:
            project.status = new_status
            project.save()
            messages.success(request, 'Statut mis à jour avec succès!')
        else:
            messages.error(request, 'Statut invalide.')
    return redirect('accounts:admin_project_detail', pk=pk)


@admin_required
def project_add_note(request, pk):
    """Ajouter un compte rendu (POST uniquement, immuable)"""
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        note_type = request.POST.get('type')
        content = request.POST.get('content', '').strip()
        valid_types = ['call', 'meeting', 'other']
        if content and note_type in valid_types:
            ProjectNote.objects.create(
                project=project,
                type=note_type,
                content=content,
                created_by=request.user,
            )
            messages.success(request, 'Compte rendu enregistré.')
        else:
            messages.error(request, 'Le contenu du compte rendu est requis.')
    return redirect('accounts:admin_project_detail', pk=pk)


@require_POST
@admin_required
def project_delete(request, pk):
    """Supprime une demande client et ses notes"""
    project = get_object_or_404(Project, pk=pk)
    name = project.contact_name
    project.delete()
    messages.success(request, f'Demande de {name} supprimée.')
    return redirect('accounts:admin_project_list')


# ========== GESTION DES PRESTATAIRES ==========

@admin_required
def vendor_list(request):
    """Liste des prestataires"""
    vendors = VendorProfile.objects.prefetch_related('cities', 'service_types').order_by('-created_at')
    is_active = request.GET.get('is_active')
    if is_active == '1':
        vendors = vendors.filter(is_active=True)
    elif is_active == '0':
        vendors = vendors.filter(is_active=False)
    paginator = Paginator(vendors, 20)
    vendors = paginator.get_page(request.GET.get('page'))
    service_types = ServiceType.objects.all().order_by('name')
    cities = City.objects.filter(is_active=True).order_by('name')
    return render(request, 'accounts/admin/vendor_list.html', {
        'vendors': vendors,
        'selected_is_active': is_active,
        'service_types': service_types,
        'cities': cities,
    })


@admin_required
def vendor_detail(request, pk):
    """Détails d'un prestataire"""
    vendor = get_object_or_404(
        VendorProfile.objects.prefetch_related('cities', 'countries', 'service_types', 'images'),
        pk=pk
    )
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_active':
            vendor.is_active = not vendor.is_active
            vendor.save()
            status = 'activé' if vendor.is_active else 'désactivé'
            messages.success(request, f'Prestataire {status} avec succès!')
        return redirect('accounts:admin_vendor_detail', pk=pk)

    cities_by_country = {}
    for country in vendor.countries.order_by('display_order', 'name'):
        cities_by_country[country] = list(vendor.cities.filter(country=country).order_by('name'))

    thirty_days_ago = timezone.now() - timedelta(days=30)
    contact_views_total = vendor.contact_views.count()
    contact_views_30d = vendor.contact_views.filter(viewed_at__gte=thirty_days_ago).count()

    return render(request, 'accounts/admin/vendor_detail.html', {
        'vendor': vendor,
        'cities_by_country': cities_by_country,
        'contact_views_total': contact_views_total,
        'contact_views_30d': contact_views_30d,
    })


@admin_required
def vendor_create(request):
    """Créer un nouveau prestataire"""
    if request.method == 'POST':
        locations_json_val = request.POST.get('locations_json', '[]')
        try:
            groups = json.loads(locations_json_val)
        except (ValueError, TypeError):
            groups = []

        def _parse_budget(val):
            try:
                return float(val) if val and val.strip() else None
            except (ValueError, TypeError):
                return None

        vendor = VendorProfile.objects.create(
            business_name=request.POST.get('business_name'),
            description=request.POST.get('description', ''),
            website=request.POST.get('website', ''),
            whatsapp=request.POST.get('whatsapp', ''),
            address=request.POST.get('address', ''),
            facebook=request.POST.get('facebook', ''),
            instagram=request.POST.get('instagram', ''),
            is_active=request.POST.get('is_active') == 'on',
            is_featured=request.POST.get('is_featured') == 'on',
            min_budget=_parse_budget(request.POST.get('min_budget')),
            max_budget=_parse_budget(request.POST.get('max_budget')),
        )
        if 'logo' in request.FILES:
            vendor.logo = request.FILES['logo']
            vendor.save()
        service_type_ids = request.POST.getlist('service_types')
        if service_type_ids:
            vendor.service_types.set(service_type_ids)
        country_ids = [g['country_id'] for g in groups if g.get('country_id')]
        city_ids = [cid for g in groups for cid in g.get('city_ids', [])]
        vendor.countries.set(country_ids)
        vendor.cities.set(city_ids)
        messages.success(request, 'Prestataire créé avec succès!')
        return redirect('accounts:admin_vendor_detail', pk=vendor.pk)

    service_types = ServiceType.objects.all().order_by('name')
    countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
    return render(request, 'accounts/admin/vendor_form.html', {
        'service_types': service_types,
        'countries': countries,
        'cities_json': _admin_build_cities_json(),
        'countries_list_json': _admin_build_countries_list_json(),
        'existing_locations_json': '[]',
    })


@admin_required
def vendor_edit(request, pk):
    """Modifier un prestataire"""
    vendor = get_object_or_404(
        VendorProfile.objects.prefetch_related('cities', 'countries', 'service_types'),
        pk=pk
    )
    if request.method == 'POST':
        vendor.business_name = request.POST.get('business_name')
        vendor.description = request.POST.get('description', '')
        vendor.website = request.POST.get('website', '')
        vendor.whatsapp = request.POST.get('whatsapp', '')
        vendor.address = request.POST.get('address', '')
        vendor.facebook = request.POST.get('facebook', '')
        vendor.instagram = request.POST.get('instagram', '')
        vendor.is_active = request.POST.get('is_active') == 'on'
        vendor.is_featured = request.POST.get('is_featured') == 'on'
        def _parse_budget(val):
            try:
                return float(val) if val and val.strip() else None
            except (ValueError, TypeError):
                return None
        vendor.min_budget = _parse_budget(request.POST.get('min_budget'))
        vendor.max_budget = _parse_budget(request.POST.get('max_budget'))
        if 'logo' in request.FILES:
            vendor.logo = request.FILES['logo']
        vendor.save()
        service_type_ids = request.POST.getlist('service_types')
        if service_type_ids:
            vendor.service_types.set(service_type_ids)

        locations_json_val = request.POST.get('locations_json', '[]')
        try:
            groups = json.loads(locations_json_val)
        except (ValueError, TypeError):
            groups = []
        country_ids = [g['country_id'] for g in groups if g.get('country_id')]
        city_ids = [cid for g in groups for cid in g.get('city_ids', [])]
        vendor.countries.set(country_ids)
        vendor.cities.set(city_ids)
        messages.success(request, 'Prestataire modifié avec succès!')
        return redirect('accounts:admin_vendor_detail', pk=pk)

    existing_groups = []
    for country in vendor.countries.order_by('display_order', 'name'):
        city_ids = list(vendor.cities.filter(country=country).values_list('id', flat=True))
        existing_groups.append({'country_id': country.id, 'city_ids': city_ids})

    service_types = ServiceType.objects.all().order_by('name')
    countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
    return render(request, 'accounts/admin/vendor_form.html', {
        'vendor': vendor,
        'service_types': service_types,
        'countries': countries,
        'cities_json': _admin_build_cities_json(),
        'countries_list_json': _admin_build_countries_list_json(),
        'existing_locations_json': json.dumps(existing_groups),
    })


@admin_required
def vendor_toggle_active(request, pk):
    vendor = get_object_or_404(VendorProfile, pk=pk)
    if request.method == 'POST':
        vendor.is_active = not vendor.is_active
        vendor.save()
        status = 'activé' if vendor.is_active else 'désactivé'
        messages.success(request, f'Prestataire {status} avec succès!')
    return redirect(request.META.get('HTTP_REFERER', 'accounts:admin_vendor_list'))


# ========== GESTION DES CANDIDATURES PRESTATAIRES ==========


@require_POST
@admin_required
def application_resize_images(request, pk):
    """Redimensionne les images portfolio d'une candidature"""
    application = get_object_or_404(VendorApplication, pk=pk)
    count = 0
    for i in range(1, 6):
        img = getattr(application, f'image_{i}')
        if img:
            resized = VendorImage._resize_image(img)
            setattr(application, f'image_{i}', resized)
            count += 1
    if count:
        application.save(update_fields=[f'image_{i}' for i in range(1, 6)] + ['updated_at'])
        messages.success(request, f'{count} image{"s" if count > 1 else ""} redimensionnée{"s" if count > 1 else ""}.')
    else:
        messages.info(request, 'Aucune image à redimensionner.')
    return redirect('accounts:admin_application_detail', pk=pk)


@require_POST
@admin_required
def application_delete(request, pk):
    """Supprime une candidature et ses images du disque"""
    import os
    application = get_object_or_404(VendorApplication, pk=pk)
    name = application.name
    for i in range(1, 6):
        img = getattr(application, f'image_{i}')
        if img:
            try:
                if os.path.isfile(img.path):
                    os.remove(img.path)
            except Exception:
                pass
    application.delete()
    messages.success(request, f'Candidature de {name} supprimée.')
    return redirect('accounts:admin_application_list')

@admin_required
def application_list(request):
    """Liste des candidatures prestataires"""
    applications = VendorApplication.objects.prefetch_related('service_types').order_by('-created_at')
    status = request.GET.get('status')
    if status:
        applications = applications.filter(status=status)
    paginator = Paginator(applications, 20)
    applications = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/admin/application_list.html', {
        'applications': applications,
        'selected_status': status,
        'status_choices': VendorApplication.STATUS_CHOICES,
    })


@admin_required
def application_detail(request, pk):
    """Détails d'une candidature prestataire"""
    application = get_object_or_404(
        VendorApplication.objects.prefetch_related('service_types'), pk=pk
    )
    if request.method == 'POST':
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '').strip()
        valid_statuses = [s[0] for s in VendorApplication.STATUS_CHOICES]
        if new_status in valid_statuses:
            application.status = new_status
            application.admin_notes = admin_notes
            application.save(update_fields=['status', 'admin_notes', 'updated_at'])
            messages.success(request, 'Candidature mise à jour.')
        else:
            messages.error(request, 'Statut invalide.')
        return redirect('accounts:admin_application_detail', pk=pk)
    return render(request, 'accounts/admin/application_detail.html', {
        'application': application,
    })


@admin_required
def application_create_profile(request, pk):
    """Crée un VendorProfile depuis une candidature approuvée et transfère les images"""
    import os
    from django.core.files.base import ContentFile

    if request.method != 'POST':
        return redirect('accounts:admin_application_detail', pk=pk)

    application = get_object_or_404(
        VendorApplication.objects.prefetch_related(
            'service_types', 'countries', 'cities'
        ),
        pk=pk,
    )

    if application.vendor_profile_id:
        messages.info(request, 'Un profil existe déjà pour cette candidature.')
        return redirect('accounts:admin_vendor_detail', pk=application.vendor_profile_id)

    vendor = VendorProfile.objects.create(
        business_name=application.business_name or application.name,
        description=application.description,
        whatsapp=application.whatsapp,
        address=application.address,
        instagram=application.instagram,
        facebook=application.facebook,
        is_active=False,
    )
    vendor.service_types.set(application.service_types.all())
    vendor.countries.set(application.countries.all())
    vendor.cities.set(application.cities.all())

    for i in range(1, 6):
        img_field = getattr(application, f'image_{i}')
        if img_field:
            try:
                img_field.open('rb')
                content = img_field.read()
                img_field.close()
                vi = VendorImage(vendor=vendor)
                vi.image = ContentFile(content, name=os.path.basename(img_field.name))
                vi.save()
            except Exception:
                pass

    application.vendor_profile = vendor
    application.save(update_fields=['vendor_profile', 'updated_at'])

    messages.success(request, f'Profil de {application.name} créé avec succès. Il est inactif — activez-le quand il est prêt.')
    return redirect('accounts:admin_vendor_detail', pk=vendor.pk)


@require_POST
@admin_required
def application_delete_image(request, pk, n):
    """Supprime l'image_N d'une candidature (n = 1..5)"""
    import os
    if n not in range(1, 6):
        return JsonResponse({'success': False, 'error': 'Slot invalide'}, status=400)
    application = get_object_or_404(VendorApplication, pk=pk)
    field_name = f'image_{n}'
    img_field = getattr(application, field_name)
    if img_field:
        try:
            if os.path.isfile(img_field.path):
                os.remove(img_field.path)
        except Exception:
            pass
        setattr(application, field_name, None)
        application.save(update_fields=[field_name, 'updated_at'])
    return JsonResponse({'success': True})


@require_POST
@admin_required
def application_add_image(request, pk):
    """Ajoute une image dans le premier slot libre d'une candidature"""
    application = get_object_or_404(VendorApplication, pk=pk)
    img = request.FILES.get('image')
    if not img:
        return JsonResponse({'success': False, 'error': 'Aucune image fournie'}, status=400)
    for i in range(1, 6):
        field_name = f'image_{i}'
        if not getattr(application, field_name):
            from apps.vendors.models import VendorImage as VI
            resized = VI._resize_image(img)
            setattr(application, field_name, resized)
            application.save(update_fields=[field_name, 'updated_at'])
            return JsonResponse({
                'success': True,
                'slot': i,
                'url': getattr(application, field_name).url,
            })
    return JsonResponse({'success': False, 'error': 'Maximum 5 images atteint'}, status=400)


@require_POST
@admin_required
def application_edit(request, pk):
    """Édite les champs texte d'une candidature"""
    application = get_object_or_404(VendorApplication, pk=pk)
    name = request.POST.get('name', '').strip()
    if name:
        application.name = name
    application.business_name = request.POST.get('business_name', '').strip()
    application.email = request.POST.get('email', '').strip()
    application.whatsapp = request.POST.get('whatsapp', '').strip()
    application.address = request.POST.get('address', '').strip()
    description = request.POST.get('description', '').strip()
    if description:
        application.description = description
    application.other_service = request.POST.get('other_service', '').strip()
    application.instagram = request.POST.get('instagram', '').strip()
    application.facebook = request.POST.get('facebook', '').strip()
    application.save(update_fields=[
        'name', 'business_name', 'email', 'whatsapp', 'address',
        'description', 'other_service', 'instagram', 'facebook', 'updated_at',
    ])
    messages.success(request, 'Candidature mise à jour.')
    return redirect('accounts:admin_application_detail', pk=pk)


@require_POST
@admin_required
def vendor_add_image(request, vendor_id):
    """Ajoute une image à un profil prestataire"""
    vendor = get_object_or_404(VendorProfile, pk=vendor_id)
    img = request.FILES.get('image')
    if not img:
        return JsonResponse({'success': False, 'error': 'Aucune image fournie'}, status=400)
    vi = VendorImage(vendor=vendor)
    vi.image = img
    vi.save()
    return JsonResponse({'success': True, 'image_id': vi.pk, 'url': vi.image.url})


@admin_required
def vendor_set_cover_image(request, vendor_id, image_id):
    """Définit une image comme couverture du profil"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    vendor = get_object_or_404(VendorProfile, pk=vendor_id)
    if not VendorImage.objects.filter(pk=image_id, vendor=vendor).exists():
        return JsonResponse({'success': False, 'error': 'Image introuvable'}, status=404)
    VendorImage.objects.filter(vendor=vendor).update(is_cover=False)
    VendorImage.objects.filter(pk=image_id).update(is_cover=True)
    return JsonResponse({'success': True})


# ========== MESSAGES DE CONTACT ==========

@admin_required
def contact_message_list(request):
    msgs = ContactMessage.objects.order_by('-created_at')
    status = request.GET.get('status')
    if status:
        msgs = msgs.filter(status=status)
    paginator = Paginator(msgs, 25)
    msgs = paginator.get_page(request.GET.get('page'))
    unread_count = ContactMessage.objects.filter(status='new').count()
    return render(request, 'accounts/admin/contact_message_list.html', {
        'messages_list': msgs,
        'selected_status': status,
        'status_choices': ContactMessage.STATUS_CHOICES,
        'unread_count': unread_count,
    })


@admin_required
def contact_message_detail(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if msg.status == 'new':
        msg.status = 'read'
        msg.save()
    if request.method == 'POST':
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '').strip()
        valid_statuses = [s[0] for s in ContactMessage.STATUS_CHOICES]
        if new_status in valid_statuses:
            msg.status = new_status
            msg.admin_notes = admin_notes
            msg.save()
            messages.success(request, 'Message mis à jour.')
        return redirect('accounts:admin_contact_message_detail', pk=pk)
    return render(request, 'accounts/admin/contact_message_detail.html', {'msg': msg})


@require_POST
@admin_required
def vendor_delete_image(request, vendor_id, image_id):
    """Supprimer une image d'un prestataire"""
    import os
    try:
        vendor = get_object_or_404(VendorProfile, pk=vendor_id)
        image = get_object_or_404(VendorImage, pk=image_id, vendor=vendor)
        if image.image and os.path.isfile(image.image.path):
            os.remove(image.image.path)
        image.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ── PUBLICITÉS ────────────────────────────────────────────────

@admin_required
def ad_list(request):
    ads = Advertisement.objects.all().order_by('zone', '-created_at')
    return render(request, 'accounts/admin/ad_list.html', {'ads': ads})


@admin_required
def ad_create(request):
    if request.method == 'POST':
        zone = request.POST.get('zone')
        link_url = request.POST.get('link_url', '').strip()
        alt_text = request.POST.get('alt_text', '').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')

        if not all([zone, alt_text, start_date, end_date, image]):
            messages.error(request, 'Tous les champs obligatoires doivent être remplis.')
            return render(request, 'accounts/admin/ad_form.html', {
                'zone_choices': Advertisement.ZONE_CHOICES,
                'form_data': request.POST,
            })

        from datetime import date as date_type
        try:
            sd = date_type.fromisoformat(start_date)
            ed = date_type.fromisoformat(end_date)
            if ed < sd:
                messages.error(request, 'La date de fin doit être postérieure à la date de début.')
                return render(request, 'accounts/admin/ad_form.html', {
                    'zone_choices': Advertisement.ZONE_CHOICES,
                    'form_data': request.POST,
                })
        except ValueError:
            messages.error(request, 'Format de date invalide.')
            return render(request, 'accounts/admin/ad_form.html', {
                'zone_choices': Advertisement.ZONE_CHOICES,
                'form_data': request.POST,
            })

        Advertisement.objects.create(
            zone=zone,
            image=image,
            link_url=link_url,
            alt_text=alt_text,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
        )
        messages.success(request, 'Publicité créée avec succès.')
        return redirect('accounts:admin_ad_list')

    return render(request, 'accounts/admin/ad_form.html', {
        'zone_choices': Advertisement.ZONE_CHOICES,
    })


@admin_required
def ad_edit(request, pk):
    ad = get_object_or_404(Advertisement, pk=pk)
    if request.method == 'POST':
        ad.zone = request.POST.get('zone')
        ad.link_url = request.POST.get('link_url', '').strip()
        ad.alt_text = request.POST.get('alt_text', '').strip()
        ad.start_date = request.POST.get('start_date')
        ad.end_date = request.POST.get('end_date')
        ad.is_active = request.POST.get('is_active') == 'on'
        if request.FILES.get('image'):
            if ad.image:
                ad.image.delete(save=False)
            ad.image = request.FILES['image']
        from datetime import date as date_type
        try:
            sd = date_type.fromisoformat(str(ad.start_date))
            ed = date_type.fromisoformat(str(ad.end_date))
            if ed < sd:
                messages.error(request, 'La date de fin doit être postérieure à la date de début.')
                return render(request, 'accounts/admin/ad_form.html', {
                    'ad': ad,
                    'zone_choices': Advertisement.ZONE_CHOICES,
                })
        except (ValueError, TypeError):
            messages.error(request, 'Format de date invalide.')
            return render(request, 'accounts/admin/ad_form.html', {
                'ad': ad,
                'zone_choices': Advertisement.ZONE_CHOICES,
            })
        ad.save()
        messages.success(request, 'Publicité mise à jour.')
        return redirect('accounts:admin_ad_list')

    return render(request, 'accounts/admin/ad_form.html', {
        'ad': ad,
        'zone_choices': Advertisement.ZONE_CHOICES,
    })


@admin_required
def ad_delete(request, pk):
    ad = get_object_or_404(Advertisement, pk=pk)
    if request.method == 'POST':
        ad.image.delete(save=False)
        ad.delete()
        messages.success(request, 'Publicité supprimée.')
        return redirect('accounts:admin_ad_list')
    return render(request, 'accounts/admin/ad_list.html', {'ads': Advertisement.objects.all()})
