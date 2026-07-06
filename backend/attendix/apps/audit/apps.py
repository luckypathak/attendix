from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendix.apps.audit'

    def ready(self):
        import attendix.apps.audit.signals
