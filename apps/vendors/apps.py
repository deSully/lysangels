from django.apps import AppConfig


class VendorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vendors'
    
    def ready(self):
        """Importer les signals au démarrage de l'application"""
        import apps.vendors.signals
