from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Project, EventType
from .forms import ProjectCreateForm, ProjectEditForm
from apps.vendors.models import ServiceType
from apps.core.cache_utils import get_cached_service_types, get_cached_event_types


@login_required
def project_create(request):
    """Création d'un nouveau projet événementiel"""
    if request.user.is_provider:
        messages.error(request, 'Les prestataires ne peuvent pas créer de projets.')
        return redirect('core:home')

    if request.method == 'POST':
        form = ProjectCreateForm(request.POST)
        
        if form.is_valid():
            # Créer le projet avec les données validées
            project = form.save(commit=False)
            project.client = request.user
            project.status = 'published'
            project.save()
            
            # Sauvegarder les relations many-to-many (services_needed)
            form.save_m2m()

            messages.success(request, 'Votre projet a été créé avec succès!')
            return redirect('projects:project_detail', pk=project.pk)
        else:
            # Form invalide - les erreurs sont dans form.errors
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ProjectCreateForm()

    # Bypass cache pour debug - récupérer directement depuis la DB
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

    context = {
        'project': project,
        'proposals': proposals,
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
