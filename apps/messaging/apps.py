from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.messaging'
    
    def ready(self):
        """Importer les signaux lors du démarrage de l'application"""
        import apps.messaging.signals
