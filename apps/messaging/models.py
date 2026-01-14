from django.db import models
from django.conf import settings
from apps.proposals.models import ProposalRequest


class Conversation(models.Model):
    """Fil de conversation entre un client et un prestataire"""
    proposal_request = models.OneToOneField(
        ProposalRequest,
        on_delete=models.CASCADE,
        related_name='conversation',
        verbose_name='Demande de devis'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation: {self.proposal_request.project.title}"

    @property
    def client(self):
        return self.proposal_request.project.client

    @property
    def vendor(self):
        return self.proposal_request.vendor

    def unread_count_for_user(self, user):
        """Retourne le nombre de messages non lus pour un utilisateur donné"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def last_message(self):
        """Retourne le dernier message de la conversation"""
        return self.messages.last()


class Message(models.Model):
    """Message dans une conversation"""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Conversation'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Expéditeur'
    )
    content = models.TextField(verbose_name='Message')
    attachment = models.FileField(
        upload_to='messages/',
        blank=True,
        null=True,
        verbose_name='Pièce jointe'
    )
    is_read = models.BooleanField(default=False, verbose_name='Lu', db_index=True)
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Lu le')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message de {self.sender.get_full_name()} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
