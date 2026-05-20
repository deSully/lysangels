import json
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from .forms import ProjectCreateForm
from apps.core.cache_utils import get_cached_service_types
from apps.core.models import City
from apps.core.turnstile import verify_turnstile
from .tasks import send_project_confirmation, notify_admin_new_project


def project_create(request):
    """Formulaire public 'J'ai un projet' — aucun compte requis"""
    cities_by_country = {}
    for c in City.objects.filter(is_active=True).select_related('country').order_by('name'):
        if c.country_id:
            cities_by_country.setdefault(str(c.country_id), []).append({'id': c.id, 'name': c.name})

    if request.method == 'POST':
        token = request.POST.get('cf-turnstile-response', '')
        if not verify_turnstile(token):
            messages.error(request, "Veuillez confirmer que vous n'êtes pas un robot.")
            form = ProjectCreateForm(request.POST)
        else:
            form = ProjectCreateForm(request.POST)
            if form.is_valid():
                project = form.save(commit=False)
                project.title = f"Projet de {project.contact_name}"
                project.status = 'new'
                project.save()
                form.save_m2m()
                if project.contact_email:
                    send_project_confirmation(project.contact_name, project.contact_email)
                notify_admin_new_project(
                    contact_name=project.contact_name,
                    contact_email=project.contact_email,
                    contact_phone=project.contact_phone,
                    event_description=project.description,
                    event_date=str(project.event_date) if project.event_date else '',
                    budget=f"{project.budget_min or '—'} – {project.budget_max or '—'} FCFA",
                )
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
        'cities_json': json.dumps(cities_by_country),
        'turnstile_sitekey': settings.TURNSTILE_SITEKEY,
    })
