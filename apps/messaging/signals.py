from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from datetime import datetime

from .models import Message


@receiver(post_save, sender=Message)
def send_new_message_notification(sender, instance, created, **kwargs):
    """
    Envoie une notification par email lorsqu'un nouveau message est créé.
    """
    if not created:
        return  # Ne rien faire si c'est une mise à jour
    
    # Ne pas envoyer d'email si c'est un message système ou si le destinataire est l'expéditeur
    conversation = instance.conversation
    
    # Déterminer le destinataire (l'autre personne dans la conversation)
    if instance.sender == conversation.client:
        recipient = conversation.vendor.user
    else:
        recipient = conversation.client
    
    # Ne pas envoyer si le destinataire est l'expéditeur (ne devrait pas arriver)
    if recipient == instance.sender:
        return
    
    # Vérifier si le destinataire a un email
    if not recipient.email:
        return
    
    # Préparer les données pour le template
    context = {
        'recipient_name': recipient.get_full_name() or recipient.username,
        'sender_name': instance.sender.get_full_name() or instance.sender.username,
        'project_title': conversation.proposal_request.project.title,
        'message_preview': instance.content[:150] + ('...' if len(instance.content) > 150 else ''),
        'conversation_url': f"{settings.SITE_URL}{reverse('messaging:conversation_detail', kwargs={'pk': conversation.pk})}",
        'site_url': settings.SITE_URL,
        'current_year': datetime.now().year,
    }
    
    try:
        # Rendre le template HTML
        html_message = render_to_string('emails/new_message.html', context)
        
        # Créer la version texte brut à partir du template texte
        plain_message = render_to_string('emails/new_message.txt', context)
        
        # Envoyer l'email
        send_mail(
            subject=f'Nouveau message de {context["sender_name"]} - LysAngels',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            html_message=html_message,
            fail_silently=True,  # Ne pas lever d'erreur si l'envoi échoue
        )
    except Exception as e:
        # Logger l'erreur mais ne pas interrompre le processus
        print(f"Erreur lors de l'envoi de l'email de notification: {e}")
        # En production, utiliser logging.error() au lieu de print()
