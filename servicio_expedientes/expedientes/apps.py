from django.apps import AppConfig

class ExpedientesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'expedientes'
    label = 'expedientes_core'

    def ready(self):
        import expedientes.signals