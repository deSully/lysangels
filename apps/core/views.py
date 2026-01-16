from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Avg, Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from apps.vendors.models import ServiceType, VendorProfile
from apps.projects.models import EventType, Project
from apps.proposals.models import Proposal
from apps.accounts.models import User
from apps.core.models import Quartier, TermsOfService, Notification, ContactMessage
from apps.core.cache_utils import get_cached_service_types, get_cached_event_types
from apps.core.forms import ContactForm
from django.contrib import messages


def home(request):
    """Page d'accueil LysAngels - Affiche uniquement les catégories de services"""
    service_types = get_cached_service_types(ordered=True)
    event_types = get_cached_event_types(limit=6)
    
    # Statistiques réelles
    total_service_types = len(service_types)
    total_vendors = VendorProfile.objects.filter(is_active=True).count()
    total_projects = Project.objects.count()
    
    # Calcul du taux de satisfaction (propositions acceptées / total propositions)
    accepted_proposals = Proposal.objects.filter(status='accepted').count()
    total_proposals = Proposal.objects.count()
    satisfaction_rate = int((accepted_proposals / total_proposals * 100)) if total_proposals > 0 else 0

    context = {
        'service_types': service_types,
        'event_types': event_types,
        'stats': {
            'service_types_count': total_service_types,
            'vendors_count': total_vendors,
            'projects_count': total_projects,
            'satisfaction_rate': satisfaction_rate,
        }
    }
    return render(request, 'core/home.html', context)


def about(request):
    """Page À propos"""
    return render(request, 'core/about.html')


def contact(request):
    """Page Contact avec formulaire"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre message a bien été envoyé. Nous vous répondrons dans les plus brefs délais.')
            return redirect('core:contact')
    else:
        form = ContactForm()

    return render(request, 'core/contact.html', {'form': form})


def how_it_works(request):
    """Page Comment ça marche"""
    return render(request, 'core/how_it_works.html')


def get_quartiers_by_city(request):
    """API pour récupérer les quartiers d'une ville"""
    city_id = request.GET.get('city')
    if not city_id:
        return JsonResponse([], safe=False)
    
    quartiers = Quartier.objects.filter(city_id=city_id, is_active=True).values('id', 'name').order_by('name')
    return JsonResponse(list(quartiers), safe=False)


def terms_of_service(request):
    """Page Conditions générales d'utilisation"""
    active_terms = TermsOfService.objects.filter(is_active=True).first()
    context = {
        'terms': active_terms,
    }
    return render(request, 'core/terms.html', context)


def privacy_policy(request):
    """Page Politique de confidentialité"""
    return render(request, 'core/privacy.html')


def legal_notice(request):
    """Page Mentions légales"""
    return render(request, 'core/legal.html')


@login_required
def notifications_list(request):
    """Liste des notifications de l'utilisateur"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 30)
    page_number = request.GET.get('page')
    notifications_page = paginator.get_page(page_number)
    
    context = {
        'notifications': notifications_page,
    }
    return render(request, 'core/notifications_list.html', context)


@login_required
@require_POST
def mark_notification_read(request, pk):
    """Marquer une notification comme lue"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    
    # Rediriger vers le lien de la notification si fourni
    if notification.link:
        return redirect(notification.link)
    return redirect('core:notifications_list')


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Marquer toutes les notifications comme lues"""
    Notification.mark_all_read(request.user)
    
    return JsonResponse({'success': True})


def offline(request):
    """Page hors ligne pour PWA"""
    return render(request, 'core/offline.html')
