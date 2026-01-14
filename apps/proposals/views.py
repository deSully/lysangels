from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from .models import ProposalRequest, Proposal
from .forms import ProposalForm, ProposalRequestForm
from apps.projects.models import Project
from apps.vendors.models import VendorProfile
from apps.messaging.models import Conversation, Message
from apps.core.validators import validate_attachment_file, check_user_storage_quota


@login_required
def send_request(request, vendor_id):
    """Envoyer une demande de devis à un prestataire"""
    if request.user.is_provider:
        messages.error(request, 'Les prestataires ne peuvent pas envoyer de demandes.')
        return redirect('core:home')

    vendor = get_object_or_404(VendorProfile, pk=vendor_id, is_active=True)

    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        message = request.POST.get('message')

        project = get_object_or_404(Project, pk=project_id, client=request.user)

        # Vérifier si une demande n'existe pas déjà
        if ProposalRequest.objects.filter(project=project, vendor=vendor).exists():
            messages.warning(request, 'Vous avez déjà envoyé une demande à ce prestataire pour ce projet.')
            return redirect('vendors:vendor_detail', pk=vendor_id)

        # Créer la demande de devis
        proposal_request = ProposalRequest.objects.create(
            project=project,
            vendor=vendor,
            message=message
        )

        # Créer automatiquement la conversation
        conversation = Conversation.objects.create(
            proposal_request=proposal_request
        )

        # Créer le premier message (le message de la demande)
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message
        )

        messages.success(request, f'Demande envoyée à {vendor.business_name}! Vous pouvez maintenant échanger via la messagerie.')
        return redirect('vendors:vendor_detail', pk=vendor_id)

    # Récupérer les projets actifs du client (publiés ou en cours)
    projects = request.user.projects.filter(status__in=['published', 'in_progress'])

    context = {
        'vendor': vendor,
        'projects': projects,
    }
    return render(request, 'proposals/send_request.html', context)


@login_required
def request_list(request):
    """Liste des demandes reçues (pour prestataires)"""
    if not request.user.is_provider:
        messages.error(request, 'Accès réservé aux prestataires.')
        return redirect('core:home')

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    requests = vendor_profile.received_requests.select_related(
        'project__client',
        'project__event_type',
        'vendor__user'
    ).order_by('-created_at')

    # Calculer les statistiques
    stats = {
        'total': requests.count(),
        'pending': requests.filter(status='pending').count(),
        'viewed': requests.filter(status='viewed').count(),
        'responded': requests.filter(status='responded').count(),
    }
    
    # Pagination avec validation
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page', '1')
    
    # Valider et limiter le numéro de page
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        elif page_number > 10000:  # Limite maximale raisonnable
            page_number = paginator.num_pages
    except (ValueError, TypeError):
        page_number = 1
    
    requests_page = paginator.get_page(page_number)

    context = {
        'requests': requests_page,
        'stats': stats,
    }
    return render(request, 'proposals/request_list.html', context)


@login_required
def request_detail(request, pk):
    """Détails d'une demande de devis"""
    proposal_request = get_object_or_404(ProposalRequest, pk=pk)

    # Vérifier les permissions - retourner 404 si non autorisé pour ne pas révéler l'existence
    if request.user.is_provider:
        if proposal_request.vendor.user != request.user:
            from django.http import Http404
            raise Http404("Demande non trouvée")

        # Marquer comme vue
        if proposal_request.status == 'pending':
            proposal_request.status = 'viewed'
            proposal_request.viewed_at = timezone.now()
            proposal_request.save()
    else:
        if proposal_request.project.client != request.user:
            from django.http import Http404
            raise Http404("Demande non trouvée")

    context = {
        'proposal_request': proposal_request,
    }
    return render(request, 'proposals/request_detail.html', context)


@login_required
def create_proposal(request, request_id):
    """Créer une proposition en réponse à une demande"""
    if not request.user.is_provider:
        messages.error(request, 'Accès réservé aux prestataires.')
        return redirect('core:home')

    proposal_request = get_object_or_404(ProposalRequest, pk=request_id)

    if proposal_request.vendor.user != request.user:
        messages.error(request, 'Accès non autorisé.')
        return redirect('vendors:dashboard')

    # Vérifier si une proposition n'existe pas déjà
    if hasattr(proposal_request, 'proposal'):
        messages.warning(request, 'Vous avez déjà envoyé une proposition pour cette demande.')
        return redirect('proposals:proposal_detail', pk=proposal_request.proposal.pk)

    if request.method == 'POST':
        form = ProposalForm(request.POST, request.FILES)
        
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.request = proposal_request
            proposal.vendor = proposal_request.vendor
            proposal.project = proposal_request.project
            
            # Vérifier le quota de stockage si un fichier est joint
            if form.cleaned_data.get('attachment'):
                try:
                    check_user_storage_quota(request.user, form.cleaned_data['attachment'].size)
                except ValidationError as e:
                    messages.error(request, str(e))
                    return render(request, 'proposals/create_proposal.html', {
                        'proposal_request': proposal_request,
                        'form': form,
                    })
            
            proposal.save()
            
            # Mettre à jour le statut de la demande
            proposal_request.status = 'responded'
            proposal_request.save()
            
            messages.success(request, 'Votre proposition a été envoyée avec succès!')
            return redirect('proposals:proposal_detail', pk=proposal.pk)
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = ProposalForm()
    
    context = {
        'proposal_request': proposal_request,
        'form': form,
    }
    return render(request, 'proposals/create_proposal.html', context)


@login_required
def proposal_detail(request, pk):
    """Détails d'une proposition"""
    proposal = get_object_or_404(Proposal, pk=pk)

    # Vérifier les permissions - retourner 404 si non autorisé
    if request.user.is_provider:
        if proposal.vendor.user != request.user:
            from django.http import Http404
            raise Http404("Proposition non trouvée")
    else:
        if proposal.project.client != request.user:
            from django.http import Http404
            raise Http404("Proposition non trouvée")

        # Marquer comme vue par le client
        if proposal.status == 'sent' and not request.user.is_provider:
            proposal.status = 'viewed'
            proposal.viewed_at = timezone.now()
            proposal.save()

    context = {
        'proposal': proposal,
    }
    return render(request, 'proposals/proposal_detail.html', context)


@login_required
def accept_proposal(request, pk):
    """Accepter une proposition (client uniquement)"""
    proposal = get_object_or_404(Proposal, pk=pk)

    # Vérifier que c'est bien le client du projet
    if proposal.project.client != request.user:
        messages.error(request, 'Accès non autorisé.')
        return redirect('accounts:dashboard')

    # Vérifier que la proposition n'est pas déjà acceptée ou refusée
    if proposal.status in ['accepted', 'rejected']:
        messages.warning(request, 'Cette proposition a déjà été traitée.')
        return redirect('proposals:proposal_detail', pk=pk)

    # Accepter la proposition
    proposal.status = 'accepted'
    proposal.save()

    messages.success(request, f'Vous avez accepté la proposition de {proposal.vendor.business_name} !')
    return redirect('proposals:proposal_detail', pk=pk)


@login_required
def reject_proposal(request, pk):
    """Refuser une proposition (client uniquement)"""
    proposal = get_object_or_404(Proposal, pk=pk)

    # Vérifier que c'est bien le client du projet
    if proposal.project.client != request.user:
        messages.error(request, 'Accès non autorisé.')
        return redirect('accounts:dashboard')

    # Vérifier que la proposition n'est pas déjà acceptée ou refusée
    if proposal.status in ['accepted', 'rejected']:
        messages.warning(request, 'Cette proposition a déjà été traitée.')
        return redirect('proposals:proposal_detail', pk=pk)

    # Refuser la proposition
    proposal.status = 'rejected'
    proposal.save()

    messages.info(request, f'Vous avez refusé la proposition de {proposal.vendor.business_name}.')
    return redirect('proposals:proposal_detail', pk=pk)
