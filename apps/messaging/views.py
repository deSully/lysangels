from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from .models import Conversation, Message
from apps.proposals.models import ProposalRequest
from apps.core.validators import validate_attachment_file, check_user_storage_quota


@login_required
def conversation_list(request):
    """Liste des conversations de l'utilisateur"""
    if request.user.is_provider:
        # Conversations où le prestataire est impliqué
        conversations = Conversation.objects.filter(
            proposal_request__vendor__user=request.user
        ).select_related(
            'proposal_request__project__client',
            'proposal_request__vendor__user'
        )
    else:
        # Conversations où le client est impliqué
        conversations = Conversation.objects.filter(
            proposal_request__project__client=request.user
        ).select_related(
            'proposal_request__project__client',
            'proposal_request__vendor__user'
        )

    # Ajouter le nombre de messages non lus pour chaque conversation
    conversations_with_unread = []
    for conversation in conversations:
        conversations_with_unread.append({
            'conversation': conversation,
            'unread_count': conversation.unread_count_for_user(request.user),
        })
    
    # Pagination
    paginator = Paginator(conversations_with_unread, 20)
    page_number = request.GET.get('page')
    conversations_page = paginator.get_page(page_number)

    context = {
        'conversations': conversations_page,
    }
    return render(request, 'messaging/conversation_list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def conversation_detail(request, pk):
    """Affichage et envoi de messages dans une conversation"""
    conversation = get_object_or_404(Conversation, pk=pk)

    # Vérifier les permissions
    is_client = conversation.client == request.user
    is_vendor = conversation.vendor.user == request.user

    if not (is_client or is_vendor):
        messages.error(request, 'Accès non autorisé.')
        return redirect('messaging:conversation_list')

    if request.method == 'POST':
        content = request.POST.get('content')

        if content:
            try:
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=content
                )

                if request.FILES.get('attachment'):
                    attachment = request.FILES['attachment']
                    
                    # Validation complète: quota + taille + MIME type + extension
                    check_user_storage_quota(request.user, attachment.size)
                    validate_attachment_file(attachment)
                    
                    message.attachment = attachment
                    message.save()

                messages.success(request, 'Message envoyé!')
                return redirect('messaging:conversation_detail', pk=pk)
            
            except ValidationError as e:
                messages.error(request, f'Pièce jointe invalide: {str(e)}')
                return redirect('messaging:conversation_detail', pk=pk)

    # Marquer les messages comme lus
    Message.objects.filter(
        conversation=conversation
    ).exclude(
        sender=request.user
    ).filter(
        is_read=False
    ).update(is_read=True, read_at=timezone.now())

    # Récupérer les messages avec optimisation (select_related sur sender)
    all_messages = conversation.messages.select_related('sender').order_by('created_at')

    context = {
        'conversation': conversation,
        'messages': all_messages,
        'is_client': is_client,
        'is_vendor': is_vendor,
    }
    return render(request, 'messaging/conversation_detail.html', context)


@login_required
def start_conversation(request, request_id):
    """Démarrer une conversation à partir d'une demande de devis"""
    proposal_request = get_object_or_404(ProposalRequest, pk=request_id)

    # Vérifier les permissions
    is_client = proposal_request.project.client == request.user
    is_vendor = proposal_request.vendor.user == request.user

    if not (is_client or is_vendor):
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:home')

    # Créer ou récupérer la conversation
    conversation, created = Conversation.objects.get_or_create(
        proposal_request=proposal_request
    )

    return redirect('messaging:conversation_detail', pk=conversation.pk)
