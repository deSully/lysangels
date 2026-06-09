import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_application_confirmation(name, email):
    def _send():
        html_body = render_to_string('emails/vendor_application_confirmation.html', {'name': name})
        msg = EmailMultiAlternatives(
            subject='Candidature reçue — LysAngels',
            body=f'Bonjour {name},\n\nNous avons bien reçu ta candidature et te recontacterons prochainement.\n\nSusy — LysAngels',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()


def send_vendor_message(vendor_name, vendor_email, subject, body, reply_url):
    """Envoie un message de l'admin à un prestataire avec lien de réponse unique"""
    def _send():
        html_body = render_to_string('emails/vendor_message.html', {
            'vendor_name': vendor_name,
            'subject': subject,
            'message_body': body,
            'reply_url': reply_url,
        })
        plain_body = (
            f"Bonjour {vendor_name},\n\n"
            f"{body}\n\n"
            f"Pour répondre, cliquez sur ce lien (valable 7 jours) :\n{reply_url}\n\n"
            f"À très bientôt,\nSusy — LysAngels\nsusy@lysangels.com"
        )
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email='Susy — LysAngels <susy@lysangels.com>',
            to=[vendor_email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()


def notify_admin_new_application(name, business_name, service_types_str, email, whatsapp):
    from apps.core.models import SiteSettings
    admin_email = SiteSettings.get().admin_notify_email
    if not admin_email:
        return

    def _send():
        lines = [
            f"Nom : {name}",
            f"Entreprise : {business_name or '—'}",
            f"Métiers : {service_types_str or '—'}",
            f"Email : {email or '—'}",
            f"WhatsApp : {whatsapp or '—'}",
        ]
        body = "Nouvelle candidature prestataire reçue sur LysAngels.\n\n" + "\n".join(lines)
        msg = EmailMultiAlternatives(
            subject=f"Nouvelle candidature — {name}",
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
        )
        msg.send()

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()
