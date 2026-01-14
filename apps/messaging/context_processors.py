"""
Context processor pour ajouter le compteur de messages non lus
"""
from apps.messaging.models import Conversation


def unread_messages_count(request):
    """Retourne le nombre total de messages non lus pour l'utilisateur connecté"""
    if not request.user.is_authenticated:
        return {'unread_messages_count': 0}
    
    # Récupérer les conversations de l'utilisateur
    if request.user.is_provider:
        conversations = Conversation.objects.filter(
            proposal_request__vendor__user=request.user
        )
    else:
        conversations = Conversation.objects.filter(
            proposal_request__project__client=request.user
        )
    
    # Compter tous les messages non lus
    total_unread = sum(
        conv.unread_count_for_user(request.user) 
        for conv in conversations
    )
    
    return {'unread_messages_count': total_unread}
