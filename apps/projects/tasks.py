from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from background_task import background


@background(schedule=0)
def send_project_confirmation(contact_name, contact_email):
    html_body = render_to_string('emails/project_confirmation.html', {'contact_name': contact_name})
    msg = EmailMultiAlternatives(
        subject='Demande reçue — LysAngels',
        body=f'Bonjour {contact_name},\n\nNous avons bien reçu ta demande et te recontacterons sous 48h.\n\nSusy — LysAngels',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[contact_email],
    )
    msg.attach_alternative(html_body, 'text/html')
    msg.send()
