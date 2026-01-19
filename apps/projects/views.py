from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Project, EventType, AdminRecommendation
from .forms import ProjectCreateForm, ProjectEditForm
from apps.vendors.models import ServiceType
from apps.core.cache_utils import get_cached_service_types, get_cached_event_types


@login_required
def project_create(request):
    """Création d'un nouveau projet événementiel (avec préremplissage possible pour un prestataire)"""
    from apps.vendors.models import VendorProfile
    vendor_id = request.GET.get('vendor_id')
    initial = {}
    preselected_vendor = None

    if vendor_id:
        try:
            preselected_vendor = VendorProfile.objects.get(pk=vendor_id, is_active=True)
            # Préremplir le service principal du prestataire
            main_services = preselected_vendor.service_types.all()
            if main_services.exists():
                initial['services_needed'] = [s.pk for s in main_services]
        except VendorProfile.DoesNotExist:
            preselected_vendor = None

    if request.user.is_provider:
        messages.error(request, 'Les prestataires ne peuvent pas créer de projets.')
        return redirect('core:home')

    if request.method == 'POST':
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.client = request.user
            project.status = 'published'
            # Enregistre la demande d'accompagnement admin event
            project.admin_event_help = form.cleaned_data.get('admin_event_help', False)
            project.save()
            form.save_m2m()

            # Si un vendor_id était présent, rediriger vers la demande de devis pour ce prestataire et ce projet (en automatique)
            if vendor_id and preselected_vendor:
                messages.success(request, 'Projet créé ! Votre demande de devis va être envoyée au prestataire.')
                return redirect(f"{reverse('proposals:send_request', kwargs={'vendor_id': preselected_vendor.pk})}?project_id={project.pk}")

            if project.admin_event_help:
                messages.success(
                    request,
                    "Votre projet a été créé avec accompagnement personnalisé. L'admin event LysAngels est votre interlocuteur unique. Vous recevrez des propositions adaptées pour chaque service demandé."
                )
            else:
                messages.success(
                    request,
                    'Votre projet a été créé avec succès ! Notre équipe Suzy analyse votre demande et vous proposera des prestataires adaptés sous 24-48h.'
                )
            return redirect('projects:project_detail', pk=project.pk)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ProjectCreateForm(initial=initial)

    event_types = list(EventType.objects.all())
    service_types = list(ServiceType.objects.all())

    context = {
        'form': form,
        'event_types': event_types,
        'service_types': service_types,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Mon espace', 'url': 'accounts:dashboard'},
            {'title': 'Créer un projet'},
        ],
        'preselected_vendor': preselected_vendor,
    }
    return render(request, 'projects/project_create.html', context)


@login_required
def project_detail(request, pk):
    """Détails d'un projet"""
    project = get_object_or_404(Project, pk=pk)

    # Vérifier les permissions
    if project.client != request.user and not request.user.is_susy_admin:
        messages.error(request, 'Vous n\'avez pas accès à ce projet.')
        return redirect('core:home')

    proposals = project.proposals.select_related('vendor__user').order_by('-created_at')

    # Récupérer les recommandations Suzy (uniquement celles envoyées)
    recommendations = project.recommendations.filter(
        status__in=['sent', 'viewed', 'contacted']
    ).select_related('vendor').order_by('-created_at')

    # Marquer les recommandations comme vues par le client
    recommendations.filter(status='sent').update(status='viewed')

    context = {
        'project': project,
        'proposals': proposals,
        'recommendations': recommendations,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Mes projets', 'url': 'projects:project_list'},
            {'title': project.title},
        ],
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_list(request):
    """Liste des projets de l'utilisateur"""
    if request.user.is_provider:
        messages.error(request, 'Accès réservé aux clients.')
        return redirect('vendors:dashboard')

    projects = request.user.projects.select_related('event_type').prefetch_related('services_needed').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(projects, 15)
    page_number = request.GET.get('page')
    projects_page = paginator.get_page(page_number)

    context = {
        'projects': projects_page,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Mes projets'},
        ],
    }
    return render(request, 'projects/project_list.html', context)


@login_required
def project_edit(request, pk):
    """Édition d'un projet"""
    project = get_object_or_404(Project, pk=pk, client=request.user)

    if request.method == 'POST':
        form = ProjectEditForm(request.POST, instance=project)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Projet mis à jour avec succès!')
            return redirect('projects:project_detail', pk=project.pk)
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = ProjectEditForm(instance=project)

    context = {
        'project': project,
        'form': form,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Mes projets', 'url': 'projects:project_list'},
            {'title': project.title, 'href': f'/projects/{project.pk}/'},
            {'title': 'Modifier'},
        ],
    }
    return render(request, 'projects/project_edit.html', context)
