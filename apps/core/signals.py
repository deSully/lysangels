from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime

from apps.proposals.models import Proposal, ProposalRequest
from apps.messaging.models import Message
from apps.core.models import Notification


@receiver(post_save, sender=Message)
def notify_new_message(sender, instance, created, **kwargs):
    """Créer une notification pour un nouveau message"""
    if not created:
        return
    
    # Déterminer le destinataire
    conversation = instance.conversation
    if instance.sender == conversation.client:
        recipient = conversation.vendor.user
    else:
        recipient = conversation.client
    
    # Ne pas notifier si c'est le même utilisateur
    if recipient == instance.sender:
        return
    
    Notification.create_notification(
        user=recipient,
        notification_type='message',
        title='Nouveau message',
        message=f'{instance.sender.get_full_name()} vous a envoyé un message',
        link=reverse('messaging:conversation_detail', kwargs={'pk': conversation.pk})
    )


@receiver(post_save, sender=Proposal)
def notify_new_proposal(sender, instance, created, **kwargs):
    """Créer une notification et envoyer un email pour une nouvelle proposition"""
    if not created:
        return
    
    # Notifier le client
    client = instance.project.client
    
    # Créer la notification
    Notification.create_notification(
        user=client,
        notification_type='proposal',
        title='Nouvelle proposition reçue',
        message=f'{instance.vendor.business_name} vous a envoyé une proposition pour "{instance.project.title}"',
        link=reverse('proposals:proposal_detail', kwargs={'pk': instance.pk})
    )
    
    # Envoyer l'email
    if client.email:
        context = {
            'client_name': client.get_full_name() or client.username,
            'vendor_name': instance.vendor.business_name,
            'project_title': instance.project.title,
            'proposal_title': instance.title,
            'price': f'{instance.price:,.0f}'.replace(',', ' '),
            'delivery_time': instance.delivery_time,
            'proposal_preview': instance.message[:200] + ('...' if len(instance.message) > 200 else ''),
            'proposal_url': f"{settings.SITE_URL}{reverse('proposals:proposal_detail', kwargs={'pk': instance.pk})}",
            'site_url': settings.SITE_URL,
            'current_year': datetime.now().year,
        }
        
        try:
            html_message = render_to_string('emails/new_proposal.html', context)
            plain_message = render_to_string('emails/new_proposal.txt', context)
            
            send_mail(
                subject=f'Nouvelle proposition de {instance.vendor.business_name} - LysAngels',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erreur envoi email proposition: {e}")


@receiver(post_save, sender=ProposalRequest)
def notify_new_request(sender, instance, created, **kwargs):
    """Créer une notification et envoyer un email pour une nouvelle demande de devis"""
    if not created:
        return
    
    # Notifier le prestataire
    vendor_user = instance.vendor.user
    
    # Créer la notification
    Notification.create_notification(
        user=vendor_user,
        notification_type='request',
        title='Nouvelle demande de devis',
        message=f'{instance.project.client.get_full_name()} vous a envoyé une demande pour "{instance.project.title}"',
        link=reverse('proposals:request_detail', kwargs={'pk': instance.pk})
    )
    
    # Envoyer l'email
    if vendor_user.email:
        context = {
            'vendor_name': instance.vendor.business_name,
            'client_name': instance.project.client.get_full_name() or instance.project.client.username,
            'project_title': instance.project.title,
            'event_type': instance.project.event_type.name,
            'event_date': instance.project.event_date.strftime('%d/%m/%Y'),
            'location': f"{instance.project.city}{', ' + instance.project.quartier.name if instance.project.quartier else ''}",
            'budget': f'{instance.project.budget_min:,.0f}'.replace(',', ' ') + (' - ' + f'{instance.project.budget_max:,.0f}'.replace(',', ' ') if instance.project.budget_max else '') + ' FCFA',
            'guests_count': instance.project.guests_count or 'Non spécifié',
            'client_message': instance.message,
            'request_url': f"{settings.SITE_URL}{reverse('proposals:request_detail', kwargs={'pk': instance.pk})}",
            'site_url': settings.SITE_URL,
            'current_year': datetime.now().year,
        }
        
        try:
            html_message = render_to_string('emails/new_request.html', context)
            plain_message = render_to_string('emails/new_request.txt', context)
            
            send_mail(
                subject=f'Nouvelle demande de {instance.project.client.get_full_name()} - LysAngels',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[vendor_user.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erreur envoi email demande: {e}")
