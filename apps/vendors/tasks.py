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
