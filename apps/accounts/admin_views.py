# Formulaire de création de proposition par l'admin event


# Décorateur pour restreindre l'accès aux admins Susy Event
"""
Vues d'administration pour le profil Admin Susy Event
"""
# Décorateur pour restreindre l'accès aux admins Susy Event
from functools import wraps
def admin_required(view_func):
    """
    Décorateur qui combine login_required et user_passes_test pour les vues basées sur fonction.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not hasattr(request.user, 'user_type') or request.user.user_type != 'admin':
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Accès réservé à l'administrateur Susy Event.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@admin_required
def admin_proposal_create(request, project_id):
    from apps.proposals.models import Proposal, ProposalRequest
    from apps.vendors.models import VendorProfile
    from decimal import Decimal
    project = get_object_or_404(Project, pk=project_id)
    vendors = VendorProfile.objects.filter(is_active=True).order_by('business_name')

    if request.method == 'POST':
        vendor_id = request.POST.get('vendor')
        price = request.POST.get('amount')
        message = request.POST.get('message')
        attachment = request.FILES.get('file')
        title = request.POST.get('title', 'Proposition personnalisée')
        description = request.POST.get('description', '')
        terms = request.POST.get('terms_and_conditions', '')
        validity_days = request.POST.get('validity_days', 30)

        vendor = get_object_or_404(VendorProfile, pk=vendor_id)

        # Create a ProposalRequest first (required for the Proposal)
        proposal_request, created = ProposalRequest.objects.get_or_create(
            project=project,
            vendor=vendor,
            defaults={
                'message': message or 'Demande créée par l\'administrateur',
                'status': 'responded',
                'created_by': request.user  # L'admin qui crée la proposition
            }
        )

        proposal = Proposal.objects.create(
            request=proposal_request,
            project=project,
            vendor=vendor,
            price=Decimal(price) if price else 0,
            message=message,
            title=title,
            description=description,
            terms_and_conditions=terms,
            validity_days=validity_days,
            attachment=attachment,
            status='sent',
        )
        messages.success(request, 'Proposition créée avec succès !')
        return redirect('accounts:admin_project_detail', pk=project_id)

    context = {
        'project': project,
        'vendors': vendors,
    }
    return render(request, 'accounts/admin/proposal_form.html', context)
"""
Vues d'administration pour le profil Admin Susy Event
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test


from django.contrib import messages
from django.db.models import Count
from django.core.paginator import Paginator

from .models import User
from apps.core.models import City, Quartier, Country, ContactMessage
from apps.vendors.models import ServiceType, VendorProfile, SubscriptionTier, Review
from apps.projects.models import EventType, Project, AdminRecommendation
from apps.proposals.models import ProposalRequest, Proposal
from apps.vendors.models import VendorProfile



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count
from django.core.paginator import Paginator

from .models import User
from apps.core.models import City, Quartier, Country, ContactMessage
from apps.vendors.models import ServiceType, VendorProfile, SubscriptionTier, Review
from apps.projects.models import EventType, Project, AdminRecommendation
from apps.proposals.models import ProposalRequest, Proposal
from apps.vendors.models import VendorProfile

@admin_required
def admin_recommendations_list(request):
    """Vue custom : liste des recommandations Suzy pour l'admin"""
    status = request.GET.get('status', '')
    recommendations = AdminRecommendation.objects.select_related('project', 'vendor', 'recommended_by')
    if status:
        recommendations = recommendations.filter(status=status)
    recommendations = recommendations.order_by('-created_at')[:100]  # Limite à 100 pour perf

    # Statuts pour filtres
    status_choices = AdminRecommendation.STATUS_CHOICES

    context = {
        'recommendations': recommendations,
        'status_choices': status_choices,
        'current_status': status,
    }
    return render(request, 'accounts/suzy_recommendations_list.html', context)


@admin_required
def admin_dashboard(request):
    """Dashboard administrateur Susy Event"""
    # Statistiques
    total_users = User.objects.count()
    total_clients = User.objects.filter(user_type='client').count()
    total_providers = User.objects.filter(user_type='provider').count()
    pending_vendors = VendorProfile.objects.filter(is_active=False).count()

    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(status__in=['published', 'in_progress']).count()
    total_proposals = Proposal.objects.count()

    total_countries = Country.objects.filter(is_active=True).count()
    total_cities = City.objects.filter(is_active=True).count()
    total_quartiers = Quartier.objects.filter(is_active=True).count()
    total_service_types = ServiceType.objects.count()
    total_event_types = EventType.objects.count()

    # Dernières activités
    recent_projects = Project.objects.select_related('client', 'event_type').order_by('-created_at')[:5]
    recent_vendors = VendorProfile.objects.select_related('user').order_by('-created_at')[:5]
    
    # Avis en attente de modération
    pending_reviews = Review.objects.filter(status='pending').select_related(
        'vendor', 'client', 'project'
    ).order_by('-created_at')[:5]

    # Messages de contact non lus
    new_contact_messages = ContactMessage.objects.filter(status='new').count()
    recent_contact_messages = ContactMessage.objects.order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'total_clients': total_clients,
        'total_providers': total_providers,
        'pending_vendors': pending_vendors,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_proposals': total_proposals,
        'total_countries': total_countries,
        'total_cities': total_cities,
        'total_quartiers': total_quartiers,
        'total_service_types': total_service_types,
        'total_event_types': total_event_types,
        'recent_projects': recent_projects,
        'recent_vendors': recent_vendors,
        'pending_reviews': pending_reviews,
        'new_contact_messages': new_contact_messages,
        'recent_contact_messages': recent_contact_messages,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


# ========== GESTION DES PAYS ==========

@admin_required
def country_list(request):
    """Liste des pays"""
    countries = Country.objects.annotate(
        city_count=Count('cities')
    ).order_by('display_order', 'name')

    context = {'countries': countries}
    return render(request, 'accounts/admin/country_list.html', context)


@admin_required
def country_create(request):
    """Créer un nouveau pays"""
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        flag_emoji = request.POST.get('flag_emoji')
        display_order = request.POST.get('display_order', 999)
        is_active = request.POST.get('is_active') == 'on'

        if Country.objects.filter(code__iexact=code).exists():
            messages.error(request, f'Un pays avec le code "{code}" existe déjà.')
        elif Country.objects.filter(name__iexact=name).exists():
            messages.error(request, f'Le pays "{name}" existe déjà.')
        else:
            Country.objects.create(
                name=name,
                code=code.upper(),
                flag_emoji=flag_emoji,
                display_order=display_order,
                is_active=is_active
            )
            messages.success(request, f'Pays "{name}" créé avec succès!')
            return redirect('accounts:admin_country_list')

    return render(request, 'accounts/admin/country_form.html')


@admin_required
def country_edit(request, pk):
    """Modifier un pays"""
    country = get_object_or_404(Country, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        flag_emoji = request.POST.get('flag_emoji')
        display_order = request.POST.get('display_order', 999)
        is_active = request.POST.get('is_active') == 'on'

        if Country.objects.filter(code__iexact=code).exclude(pk=pk).exists():
            messages.error(request, f'Un pays avec le code "{code}" existe déjà.')
        elif Country.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, f'Le pays "{name}" existe déjà.')
        else:
            country.name = name
            country.code = code.upper()
            country.flag_emoji = flag_emoji
            country.display_order = display_order
            country.is_active = is_active
            country.save()
            messages.success(request, f'Pays "{name}" modifié avec succès!')
            return redirect('accounts:admin_country_list')

    context = {'country': country}
    return render(request, 'accounts/admin/country_form.html', context)


@admin_required
def country_delete(request, pk):
    """Supprimer un pays"""
    country = get_object_or_404(Country, pk=pk)

    if request.method == 'POST':
        country_name = country.name
        try:
            country.delete()
            messages.success(request, f'Pays "{country_name}" supprimé avec succès!')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer ce pays: {str(e)}')
        return redirect('accounts:admin_country_list')

    # Compter les dépendances
    city_count = country.cities.count()
    vendor_count = country.vendor_countries.count()
    
    context = {
        'country': country,
        'city_count': city_count,
        'vendor_count': vendor_count,
    }
    return render(request, 'accounts/admin/country_confirm_delete.html', context)


# ========== GESTION DES VILLES ==========

@admin_required
def city_list(request):
    """Liste des villes"""
    cities = City.objects.annotate(
        quartier_count=Count('quartiers'),
        vendor_count=Count('vendors')
    ).order_by('name')

    context = {'cities': cities}
    return render(request, 'accounts/admin/city_list.html', context)


@admin_required
def city_create(request):
    """Créer une nouvelle ville"""
    if request.method == 'POST':
        name = request.POST.get('name')
        country_id = request.POST.get('country')
        is_active = request.POST.get('is_active') == 'on'
        
        # Le pays est obligatoire
        if not country_id:
            messages.error(request, 'Le pays est obligatoire.')
            return redirect('accounts:admin_city_create')
        
        country = get_object_or_404(Country, pk=country_id)

        if City.objects.filter(name__iexact=name, country=country).exists():
            messages.error(request, f'Cette ville existe déjà dans {country.name}.')
        else:
            City.objects.create(name=name, country=country, is_active=is_active)
            messages.success(request, f'Ville "{name}" créée avec succès!')
            return redirect('accounts:admin_city_list')
    
    # Récupérer les pays pour le formulaire
    countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
    context = {'countries': countries}
    return render(request, 'accounts/admin/city_form.html', context)


@admin_required
def city_edit(request, pk):
    """Modifier une ville"""
    city = get_object_or_404(City, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        country_id = request.POST.get('country')
        is_active = request.POST.get('is_active') == 'on'
        
        if not country_id:
            messages.error(request, 'Le pays est obligatoire.')
            return redirect('accounts:admin_city_edit', pk=pk)
        
        country = get_object_or_404(Country, pk=country_id)

        if City.objects.filter(name__iexact=name, country=country).exclude(pk=pk).exists():
            messages.error(request, f'Cette ville existe déjà dans {country.name}.')
        else:
            city.name = name
            city.country = country
            city.is_active = is_active
            city.save()
            messages.success(request, f'Ville "{name}" modifiée avec succès!')
            return redirect('accounts:admin_city_list')
    
    countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
    context = {'city': city, 'countries': countries}
    return render(request, 'accounts/admin/city_form.html', context)


@admin_required
def city_delete(request, pk):
    """Supprimer une ville"""
    city = get_object_or_404(City, pk=pk)

    if request.method == 'POST':
        city_name = city.name
        try:
            city.delete()
            messages.success(request, f'Ville "{city_name}" supprimée avec succès!')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer cette ville: {str(e)}')
        return redirect('accounts:admin_city_list')

    context = {'city': city}
    return render(request, 'accounts/admin/city_confirm_delete.html', context)


# ========== GESTION DES QUARTIERS ==========

@admin_required
def quartier_list(request):
    """Liste des quartiers"""
    quartiers = Quartier.objects.select_related('city').annotate(
        vendor_count=Count('vendors')
    ).order_by('city__name', 'name')

    # Filtre par ville
    city_id = request.GET.get('city')
    if city_id:
        quartiers = quartiers.filter(city_id=city_id)

    cities = City.objects.filter(is_active=True).order_by('name')

    context = {
        'quartiers': quartiers,
        'cities': cities,
        'selected_city': city_id,
    }
    return render(request, 'accounts/admin/quartier_list.html', context)


@admin_required
def quartier_create(request):
    """Créer un nouveau quartier"""
    if request.method == 'POST':
        city_id = request.POST.get('city')
        name = request.POST.get('name')
        is_active = request.POST.get('is_active') == 'on'

        city = get_object_or_404(City, pk=city_id)

        if Quartier.objects.filter(city=city, name__iexact=name).exists():
            messages.error(request, f'Le quartier "{name}" existe déjà dans {city.name}.')
        else:
            Quartier.objects.create(city=city, name=name, is_active=is_active)
            messages.success(request, f'Quartier "{name}" créé avec succès!')
            return redirect('accounts:admin_quartier_list')

    cities = City.objects.filter(is_active=True).order_by('name')
    context = {'cities': cities}
    return render(request, 'accounts/admin/quartier_form.html', context)


@admin_required
def quartier_edit(request, pk):
    """Modifier un quartier"""
    quartier = get_object_or_404(Quartier, pk=pk)

    if request.method == 'POST':
        city_id = request.POST.get('city')
        name = request.POST.get('name')
        is_active = request.POST.get('is_active') == 'on'

        city = get_object_or_404(City, pk=city_id)

        if Quartier.objects.filter(city=city, name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, f'Le quartier "{name}" existe déjà dans {city.name}.')
        else:
            quartier.city = city
            quartier.name = name
            quartier.is_active = is_active
            quartier.save()
            messages.success(request, f'Quartier "{name}" modifié avec succès!')
            return redirect('accounts:admin_quartier_list')

    cities = City.objects.filter(is_active=True).order_by('name')
    context = {'quartier': quartier, 'cities': cities}
    return render(request, 'accounts/admin/quartier_form.html', context)


@admin_required
def quartier_delete(request, pk):
    """Supprimer un quartier"""
    quartier = get_object_or_404(Quartier, pk=pk)

    if request.method == 'POST':
        quartier_name = quartier.name
        try:
            quartier.delete()
            messages.success(request, f'Quartier "{quartier_name}" supprimé avec succès!')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer ce quartier: {str(e)}')
        return redirect('accounts:admin_quartier_list')

    context = {'quartier': quartier}
    return render(request, 'accounts/admin/quartier_confirm_delete.html', context)


# ========== GESTION DES TYPES DE SERVICES ==========

@admin_required
def service_type_list(request):
    """Liste des types de services"""
    service_types = ServiceType.objects.annotate(
        vendor_count=Count('vendors')
    ).order_by('name')

    context = {'service_types': service_types}
    return render(request, 'accounts/admin/service_type_list.html', context)


@admin_required
def service_type_create(request):
    """Créer un nouveau type de service"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', '')

        if ServiceType.objects.filter(name__iexact=name).exists():
            messages.error(request, 'Ce type de service existe déjà.')
        else:
            ServiceType.objects.create(name=name, description=description, icon=icon)
            messages.success(request, f'Type de service "{name}" créé avec succès!')
            return redirect('accounts:admin_service_type_list')

    return render(request, 'accounts/admin/service_type_form.html')


@admin_required
def service_type_edit(request, pk):
    """Modifier un type de service"""
    service_type = get_object_or_404(ServiceType, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', '')

        if ServiceType.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, 'Ce type de service existe déjà.')
        else:
            service_type.name = name
            service_type.description = description
            service_type.icon = icon
            service_type.save()
            messages.success(request, f'Type de service "{name}" modifié avec succès!')
            return redirect('accounts:admin_service_type_list')

    context = {'service_type': service_type}
    return render(request, 'accounts/admin/service_type_form.html', context)


@admin_required
def service_type_delete(request, pk):
    """Supprimer un type de service"""
    service_type = get_object_or_404(ServiceType, pk=pk)

    if request.method == 'POST':
        service_name = service_type.name
        try:
            service_type.delete()
            messages.success(request, f'Type de service "{service_name}" supprimé avec succès!')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer ce type de service: {str(e)}')
        return redirect('accounts:admin_service_type_list')

    context = {'service_type': service_type}
    return render(request, 'accounts/admin/service_type_confirm_delete.html', context)


# ========== GESTION DES TYPES D'ÉVÉNEMENTS ==========

@admin_required
def event_type_list(request):
    """Liste des types d'événements"""
    event_types = EventType.objects.annotate(
        project_count=Count('projects')
    ).order_by('name')

    context = {'event_types': event_types}
    return render(request, 'accounts/admin/event_type_list.html', context)


@admin_required
def event_type_create(request):
    """Créer un nouveau type d'événement"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', '')

        if EventType.objects.filter(name__iexact=name).exists():
            messages.error(request, 'Ce type d\'événement existe déjà.')
        else:
            EventType.objects.create(name=name, description=description, icon=icon)
            messages.success(request, f'Type d\'événement "{name}" créé avec succès!')
            return redirect('accounts:admin_event_type_list')

    return render(request, 'accounts/admin/event_type_form.html')


@admin_required
def event_type_edit(request, pk):
    """Modifier un type d'événement"""
    event_type = get_object_or_404(EventType, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', '')

        if EventType.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, 'Ce type d\'événement existe déjà.')
        else:
            event_type.name = name
            event_type.description = description
            event_type.icon = icon
            event_type.save()
            messages.success(request, f'Type d\'événement "{name}" modifié avec succès!')
            return redirect('accounts:admin_event_type_list')

    context = {'event_type': event_type}
    return render(request, 'accounts/admin/event_type_form.html', context)


@admin_required
def event_type_delete(request, pk):
    """Supprimer un type d'événement"""
    event_type = get_object_or_404(EventType, pk=pk)

    if request.method == 'POST':
        event_name = event_type.name
        try:
            event_type.delete()
            messages.success(request, f'Type d\'événement "{event_name}" supprimé avec succès!')
        except Exception as e:
            messages.error(request, f'Impossible de supprimer ce type d\'événement: {str(e)}')
        return redirect('accounts:admin_event_type_list')

    context = {'event_type': event_type}
    return render(request, 'accounts/admin/event_type_confirm_delete.html', context)


# ========== GESTION DES PROJETS ==========

@admin_required
def project_list(request):
    """Liste des projets"""
    projects = Project.objects.select_related('client', 'event_type').order_by('-created_at')

    # Filtres
    status = request.GET.get('status')
    if status:
        projects = projects.filter(status=status)

    # Filtre accompagnement admin event
    admin_event_only = request.GET.get('admin_event_help')
    if admin_event_only == '1':
        projects = projects.filter(admin_event_help=True)

    # Pagination
    paginator = Paginator(projects, 20)
    page = request.GET.get('page')
    projects = paginator.get_page(page)

    context = {
        'projects': projects,
        'selected_status': status,
        'admin_event_only': admin_event_only,
    }
    return render(request, 'accounts/admin/project_list.html', context)


@admin_required
def project_detail(request, pk):
    """Détails d'un projet"""
    project = get_object_or_404(Project.objects.select_related('client', 'event_type'), pk=pk)
    
    # Charger les propositions avec leurs informations complètes
    proposals = project.proposals.select_related('vendor', 'request').all()

    context = {
        'project': project,
        'proposals': proposals,
    }
    return render(request, 'accounts/admin/project_detail.html', context)


# ========== GESTION DES PRESTATAIRES ==========

@admin_required
def vendor_list(request):
    """Liste des prestataires"""
    vendors = VendorProfile.objects.select_related('user', 'city', 'quartier').prefetch_related('service_types').order_by('-created_at')

    # Filtres
    is_active = request.GET.get('is_active')
    service_type_ids = request.GET.getlist('service_types')  # Liste de IDs
    city_ids = request.GET.getlist('cities')  # Liste de IDs
    quartier_ids = request.GET.getlist('quartiers')  # Liste de IDs

    if is_active == '1':
        vendors = vendors.filter(is_active=True)
    elif is_active == '0':
        vendors = vendors.filter(is_active=False)

    if service_type_ids:
        vendors = vendors.filter(service_types__id__in=service_type_ids).distinct()

    if city_ids:
        vendors = vendors.filter(city_id__in=city_ids)

    if quartier_ids:
        vendors = vendors.filter(quartier_id__in=quartier_ids)

    # Pagination
    paginator = Paginator(vendors, 20)
    page = request.GET.get('page')
    vendors = paginator.get_page(page)

    # Données pour les filtres
    service_types = ServiceType.objects.all().order_by('name')
    cities = City.objects.filter(is_active=True).order_by('name')
    quartiers = Quartier.objects.filter(is_active=True).select_related('city').order_by('city__name', 'name')

    context = {
        'vendors': vendors,
        'selected_is_active': is_active,
        'selected_service_types': service_type_ids,
        'selected_cities': city_ids,
        'selected_quartiers': quartier_ids,
        'service_types': service_types,
        'cities': cities,
        'quartiers': quartiers,
    }
    return render(request, 'accounts/admin/vendor_list.html', context)


@admin_required
def vendor_detail(request, pk):
    """Détails d'un prestataire"""
    vendor = get_object_or_404(
        VendorProfile.objects.select_related('user', 'city', 'quartier').prefetch_related('service_types', 'images'),
        pk=pk
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_active':
            vendor.is_active = not vendor.is_active
            vendor.save()
            status = 'activé' if vendor.is_active else 'désactivé'
            messages.success(request, f'Prestataire {status} avec succès!')
        elif action == 'toggle_featured':
            vendor.is_featured = not vendor.is_featured
            vendor.save()
            status = 'mis en avant' if vendor.is_featured else 'retiré de la mise en avant'
            messages.success(request, f'Prestataire {status} avec succès!')
        return redirect('accounts:admin_vendor_detail', pk=pk)

    context = {'vendor': vendor}
    return render(request, 'accounts/admin/vendor_detail.html', context)


@admin_required
def vendor_create(request):
    """Créer un nouveau prestataire"""
    if request.method == 'POST':
        # Créer l'utilisateur
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')

        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé.')
        else:
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                user_type='provider'
            )

            # Créer le profil prestataire
            business_name = request.POST.get('business_name')
            description = request.POST.get('description')
            city_id = request.POST.get('city')
            quartier_id = request.POST.get('quartier')
            address = request.POST.get('address', '')
            website = request.POST.get('website', '')
            whatsapp = request.POST.get('whatsapp', '')
            facebook = request.POST.get('facebook', '')
            instagram = request.POST.get('instagram', '')
            min_budget = request.POST.get('min_budget', None)
            max_budget = request.POST.get('max_budget', None)
            is_active = request.POST.get('is_active') == 'on'
            is_featured = request.POST.get('is_featured') == 'on'

            city = get_object_or_404(City, pk=city_id) if city_id else None
            quartier = get_object_or_404(Quartier, pk=quartier_id) if quartier_id else None

            google_maps_link = request.POST.get('google_maps_link', '')

            # Abonnement
            subscription_tier_id = request.POST.get('subscription_tier')
            subscription_tier = get_object_or_404(SubscriptionTier, pk=subscription_tier_id) if subscription_tier_id else None

            subscription_expires = request.POST.get('subscription_expires_at')
            subscription_expires_at = None
            if subscription_expires:
                from django.utils.dateparse import parse_datetime
                subscription_expires_at = parse_datetime(subscription_expires)

            vendor = VendorProfile.objects.create(
                user=user,
                business_name=business_name,
                description=description,
                city=city,
                quartier=quartier,
                address=address,
                google_maps_link=google_maps_link,
                website=website,
                whatsapp=whatsapp,
                facebook=facebook,
                instagram=instagram,
                min_budget=min_budget if min_budget else None,
                max_budget=max_budget if max_budget else None,
                subscription_tier=subscription_tier,
                subscription_expires_at=subscription_expires_at,
                is_active=is_active,
                is_featured=is_featured
            )

            # Ajouter le logo si fourni
            if 'logo' in request.FILES:
                vendor.logo = request.FILES['logo']
                vendor.save()

            # Ajouter les types de services
            service_type_ids = request.POST.getlist('service_types')
            if service_type_ids:
                vendor.service_types.set(service_type_ids)
            
            # Ajouter les pays
            from apps.core.models import Country
            country_ids = request.POST.getlist('countries')
            if country_ids:
                vendor.countries.set(country_ids)
            else:
                # Si aucun pays sélectionné, assigner le Togo par défaut
                default_country = Country.objects.filter(code='TG').first()
                if default_country:
                    vendor.countries.set([default_country])

            messages.success(request, f'Prestataire "{business_name}" créé avec succès!')
            return redirect('accounts:admin_vendor_detail', pk=vendor.pk)

    # GET - Afficher le formulaire
    from apps.core.models import Country
    cities = City.objects.filter(is_active=True).order_by('name')
    service_types = ServiceType.objects.all().order_by('name')
    subscription_tiers = SubscriptionTier.objects.all().order_by('display_priority')
    countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')

    context = {
        'cities': cities,
        'service_types': service_types,
        'subscription_tiers': subscription_tiers,
        'countries': countries,
    }
    return render(request, 'accounts/admin/vendor_form.html', context)


@admin_required
def vendor_edit(request, pk):
    """Modifier un prestataire"""
    vendor = get_object_or_404(
        VendorProfile.objects.select_related('user', 'city', 'quartier').prefetch_related('service_types'),
        pk=pk
    )

    if request.method == 'POST':
        # Mettre à jour l'utilisateur
        vendor.user.email = request.POST.get('email')
        vendor.user.first_name = request.POST.get('first_name', '')
        vendor.user.last_name = request.POST.get('last_name', '')
        vendor.user.phone = request.POST.get('phone', '')
        
        # Mettre à jour le mot de passe si fourni
        password = request.POST.get('password')
        if password:
            vendor.user.set_password(password)
        
        vendor.user.save()

        # Mettre à jour le profil prestataire
        vendor.business_name = request.POST.get('business_name')
        vendor.description = request.POST.get('description')
        
        city_id = request.POST.get('city')
        quartier_id = request.POST.get('quartier')
        vendor.city = get_object_or_404(City, pk=city_id) if city_id else None
        vendor.quartier = get_object_or_404(Quartier, pk=quartier_id) if quartier_id else None
        
        vendor.address = request.POST.get('address', '')
        vendor.google_maps_link = request.POST.get('google_maps_link', '')
        vendor.website = request.POST.get('website', '')
        vendor.whatsapp = request.POST.get('whatsapp', '')
        vendor.facebook = request.POST.get('facebook', '')
        vendor.instagram = request.POST.get('instagram', '')
        
        min_budget = request.POST.get('min_budget')
        max_budget = request.POST.get('max_budget')
        vendor.min_budget = min_budget if min_budget else None
        vendor.max_budget = max_budget if max_budget else None
        
        vendor.is_active = request.POST.get('is_active') == 'on'
        vendor.is_featured = request.POST.get('is_featured') == 'on'
        
        # Mettre à jour l'abonnement
        subscription_tier_id = request.POST.get('subscription_tier')
        if subscription_tier_id:
            vendor.subscription_tier_id = subscription_tier_id
        else:
            vendor.subscription_tier = None
        
        subscription_expires = request.POST.get('subscription_expires_at')
        if subscription_expires:
            from django.utils.dateparse import parse_datetime
            vendor.subscription_expires_at = parse_datetime(subscription_expires)
        else:
            vendor.subscription_expires_at = None
        
        # Mettre à jour le logo si fourni
        if 'logo' in request.FILES:
            vendor.logo = request.FILES['logo']
        
        # Gérer les nouvelles images uploadées par l'admin
        if 'images' in request.FILES:
            from apps.vendors.models import VendorImage
            images = request.FILES.getlist('images')
            
            # Vérifier la limite d'images selon l'abonnement
            current_count = vendor.images.count()
            max_images = vendor.subscription_tier.max_images if vendor.subscription_tier else 5
            
            for image_file in images:
                if current_count >= max_images:
                    messages.warning(request, f'Limite d\'images atteinte ({max_images}). Certaines images n\'ont pas été ajoutées.')
                    break
                
                try:
                    VendorImage.objects.create(vendor=vendor, image=image_file)
                    current_count += 1
                except Exception as e:
                    messages.error(request, f'Erreur lors de l\'upload de {image_file.name}: {str(e)}')
        
        vendor.save()

        # Mettre à jour les types de services
        service_type_ids = request.POST.getlist('service_types')
        if service_type_ids:
            vendor.service_types.set(service_type_ids)
        
        # Mettre à jour les pays
        country_ids = request.POST.getlist('countries')
        if country_ids:
            vendor.countries.set(country_ids)

        messages.success(request, f'Prestataire "{vendor.business_name}" modifié avec succès!')
        return redirect('accounts:admin_vendor_detail', pk=pk)

    # GET - Afficher le formulaire
    cities = City.objects.filter(is_active=True).order_by('name')
    quartiers = Quartier.objects.filter(is_active=True).order_by('name')
    service_types = ServiceType.objects.all().order_by('name')
    subscription_tiers = SubscriptionTier.objects.all().order_by('display_priority')
    countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')

    context = {
        'vendor': vendor,
        'cities': cities,
        'quartiers': quartiers,
        'service_types': service_types,
        'subscription_tiers': subscription_tiers,
        'countries': countries,
    }
    return render(request, 'accounts/admin/vendor_form.html', context)


# ========== GESTION DES DEMANDES DE DEVIS ==========

@admin_required
def proposal_request_list(request):
    """Liste des demandes de devis"""
    requests = ProposalRequest.objects.select_related('project__client', 'vendor').order_by('-created_at')

    # Filtres
    status = request.GET.get('status')
    if status:
        requests = requests.filter(status=status)

    # Pagination
    paginator = Paginator(requests, 20)
    page = request.GET.get('page')
    requests = paginator.get_page(page)

    context = {'requests': requests, 'selected_status': status}
    return render(request, 'accounts/admin/proposal_request_list.html', context)


@admin_required
def proposal_list(request):
    """Liste des propositions"""
    proposals = Proposal.objects.select_related('request__project__client', 'request__vendor').order_by('-created_at')

    # Filtres
    status = request.GET.get('status')
    if status:
        proposals = proposals.filter(status=status)

    # Pagination
    paginator = Paginator(proposals, 20)
    page = request.GET.get('page')
    proposals = paginator.get_page(page)

    context = {'proposals': proposals, 'selected_status': status}
    return render(request, 'accounts/admin/proposal_list.html', context)


@admin_required
def vendor_toggle_active(request, pk):
    """Activer/Désactiver rapidement un prestataire"""
    vendor = get_object_or_404(VendorProfile, pk=pk)
    
    if request.method == 'POST':
        vendor.is_active = not vendor.is_active
        vendor.save()
        
        status = 'activé' if vendor.is_active else 'désactivé'
        messages.success(request, f'Prestataire "{vendor.business_name}" {status} avec succès!')
    
    # Rediriger vers la page précédente ou la liste
    return redirect(request.META.get('HTTP_REFERER', 'accounts:admin_vendor_list'))


@admin_required
def vendor_delete_image(request, vendor_id, image_id):
    """Supprimer une image d'un prestataire (modération admin)"""
    from django.http import JsonResponse
    from apps.vendors.models import VendorImage
    import os

    if request.method == 'POST':
        try:
            vendor = get_object_or_404(VendorProfile, pk=vendor_id)
            image = get_object_or_404(VendorImage, pk=image_id, vendor=vendor)

            # Supprimer le fichier physique
            if image.image and os.path.isfile(image.image.path):
                os.remove(image.image.path)

            # Supprimer l'entrée en base
            image.delete()

            return JsonResponse({'success': True, 'message': 'Image supprimée avec succès'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


# ========== GESTION DES MESSAGES DE CONTACT ==========

@admin_required
def contact_message_list(request):
    """Liste des messages de contact"""
    contact_messages = ContactMessage.objects.all().order_by('-created_at')

    # Filtres
    status = request.GET.get('status')
    subject = request.GET.get('subject')

    if status:
        contact_messages = contact_messages.filter(status=status)
    if subject:
        contact_messages = contact_messages.filter(subject=subject)

    # Compteurs pour les badges
    new_count = ContactMessage.objects.filter(status='new').count()

    # Pagination
    paginator = Paginator(contact_messages, 20)
    page = request.GET.get('page')
    contact_messages = paginator.get_page(page)

    context = {
        'contact_messages': contact_messages,
        'selected_status': status,
        'selected_subject': subject,
        'new_count': new_count,
        'status_choices': ContactMessage.STATUS_CHOICES,
        'subject_choices': ContactMessage.SUBJECT_CHOICES,
    }
    return render(request, 'accounts/admin/contact_message_list.html', context)


@admin_required
def contact_message_detail(request, pk):
    """Détail d'un message de contact"""
    contact_message = get_object_or_404(ContactMessage, pk=pk)

    # Marquer comme lu automatiquement
    if contact_message.status == 'new':
        contact_message.status = 'read'
        contact_message.save()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(ContactMessage.STATUS_CHOICES):
                contact_message.status = new_status
                contact_message.save()
                messages.success(request, 'Statut mis à jour.')

        elif action == 'save_notes':
            contact_message.admin_notes = request.POST.get('admin_notes', '')
            contact_message.save()
            messages.success(request, 'Notes enregistrées.')

        elif action == 'delete':
            contact_message.delete()
            messages.success(request, 'Message supprimé.')
            return redirect('accounts:admin_contact_message_list')

        return redirect('accounts:admin_contact_message_detail', pk=pk)

    context = {
        'contact_message': contact_message,
        'status_choices': ContactMessage.STATUS_CHOICES,
    }
    return render(request, 'accounts/admin/contact_message_detail.html', context)
