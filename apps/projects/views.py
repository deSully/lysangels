from django.shortcuts import render
from django.contrib import messages
from .models import EventType
from .forms import ProjectCreateForm
from apps.vendors.models import ServiceType


def project_create(request):
    """Formulaire public 'J'ai besoin d'aide' — aucun compte requis"""
    if request.method == 'POST':
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.status = 'new'
            project.save()
            form.save_m2m()
            return render(request, 'projects/project_create_success.html', {
                'contact_name': project.contact_name,
            })
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ProjectCreateForm()

    event_types = list(EventType.objects.all())
    service_types = list(ServiceType.objects.all())

    context = {
        'form': form,
        'event_types': event_types,
        'service_types': service_types,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'J\'ai besoin d\'aide'},
        ],
    }
    return render(request, 'projects/project_create.html', context)
