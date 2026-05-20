import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_project_confirmation(contact_name, contact_email):
    def _send():
        html_body = render_to_string('emails/project_confirmation.html', {'contact_name': contact_name})
        msg = EmailMultiAlternatives(
            subject='Demande reçue — LysAngels',
            body=f'Bonjour {contact_name},\n\nNous avons bien reçu ta demande et te recontacterons sous 48h.\n\nSusy — LysAngels',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact_email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()


def notify_admin_new_project(contact_name, contact_email, contact_phone, event_description, event_date, budget):
    from apps.core.models import SiteSettings
    admin_email = SiteSettings.get().admin_notify_email
    if not admin_email:
        return

    def _send():
        lines = [
            f"Nom : {contact_name}",
            f"Email : {contact_email or '—'}",
            f"Téléphone : {contact_phone or '—'}",
            f"Description : {event_description or '—'}",
            f"Date : {event_date or '—'}",
            f"Budget : {budget or '—'}",
        ]
        body = "Nouveau projet reçu sur LysAngels.\n\n" + "\n".join(lines)
        msg = EmailMultiAlternatives(
            subject=f"Nouveau projet — {contact_name}",
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
        )
        msg.send()

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()
