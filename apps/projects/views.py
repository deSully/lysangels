from django.shortcuts import render
from django.contrib import messages
from .forms import ProjectCreateForm
from apps.core.cache_utils import get_cached_service_types
from .tasks import send_project_confirmation


def project_create(request):
    """Formulaire public 'J'ai un projet' — aucun compte requis"""
    if request.method == 'POST':
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.title = f"Projet de {project.contact_name}"
            project.status = 'new'
            project.save()
            form.save_m2m()
            if project.contact_email:
                send_project_confirmation(project.contact_name, project.contact_email)
            return render(request, 'projects/project_create_success.html', {
                'contact_name': project.contact_name,
            })
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ProjectCreateForm()

    return render(request, 'projects/project_create.html', {
        'form': form,
        'service_types': get_cached_service_types(ordered=True),
    })
