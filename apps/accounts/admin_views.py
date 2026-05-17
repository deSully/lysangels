"""
Vues d'administration pour LysAngels
"""
import json
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count
from django.core.paginator import Paginator
from django.http import JsonResponse

from apps.core.models import City, Country, ContactMessage
from apps.vendors.models import ServiceType, VendorProfile, VendorImage, VendorApplication
from apps.projects.models import EventType, Project, ProjectNote


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
    """Dashboard administrateur"""
    from datetime import timedelta
    from django.utils import timezone

    now = timezone.now()
    last_30_days = now - timedelta(days=30)

    # Stats prestataires
    pending_vendors = VendorProfile.objects.filter(is_active=False).count()
    active_vendors = VendorProfile.objects.filter(is_active=True).count()

    # Stats demandes clients
    total_projects = Project.objects.count()
    new_projects = Project.objects.filter(status='new').count()
    projects_this_month = Project.objects.filter(created_at__gte=last_30_days).count()

    # Stats configuration
    total_countries = Country.objects.filter(is_active=True).count()
    total_cities = City.objects.filter(is_active=True).count()
    total_service_types = ServiceType.objects.count()
    total_event_types = EventType.objects.count()

    # Nouvelles demandes récentes
    recent_projects = Project.objects.filter(
        status='new'
    ).order_by('-created_at')[:10]

    recent_vendors = VendorProfile.objects.prefetch_related('cities').order_by('-created_at')[:5]

    context = {
        'pending_vendors': pending_vendors,
        'active_vendors': active_vendors,
        'total_projects': total_projects,
        'new_projects': new_projects,
        'projects_this_month': projects_this_month,
        'total_countries': total_countries,
        'total_cities': total_cities,
        'total_service_types': total_service_types,
        'total_event_types': total_event_types,
        'recent_projects': recent_projects,
        'recent_vendors': recent_vendors,
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
        ServiceType.objects.create(name=name, description=description, icon=icon)
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

    return render(request, 'accounts/admin/vendor_detail.html', {
        'vendor': vendor,
        'cities_by_country': cities_by_country,
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
        business_name=application.name,
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


@admin_required
def application_delete_image(request, pk, n):
    """Supprime l'image_N d'une candidature (n = 1..5)"""
    import os
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
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


@admin_required
def application_add_image(request, pk):
    """Ajoute une image dans le premier slot libre d'une candidature"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
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


@admin_required
def application_edit(request, pk):
    """Édite les champs texte d'une candidature"""
    if request.method != 'POST':
        return redirect('accounts:admin_application_detail', pk=pk)
    application = get_object_or_404(VendorApplication, pk=pk)
    name = request.POST.get('name', '').strip()
    if name:
        application.name = name
    application.email = request.POST.get('email', '').strip()
    application.whatsapp = request.POST.get('whatsapp', '').strip()
    application.address = request.POST.get('address', '').strip()
    description = request.POST.get('description', '').strip()
    if description:
        application.description = description
    application.instagram = request.POST.get('instagram', '').strip()
    application.facebook = request.POST.get('facebook', '').strip()
    application.save(update_fields=[
        'name', 'email', 'whatsapp', 'address',
        'description', 'instagram', 'facebook', 'updated_at',
    ])
    messages.success(request, 'Candidature mise à jour.')
    return redirect('accounts:admin_application_detail', pk=pk)


@admin_required
def vendor_add_image(request, vendor_id):
    """Ajoute une image à un profil prestataire"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
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


@admin_required
def vendor_delete_image(request, vendor_id, image_id):
    """Supprimer une image d'un prestataire"""
    import os
    if request.method == 'POST':
        try:
            vendor = get_object_or_404(VendorProfile, pk=vendor_id)
            image = get_object_or_404(VendorImage, pk=image_id, vendor=vendor)
            if image.image and os.path.isfile(image.image.path):
                os.remove(image.image.path)
            image.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
