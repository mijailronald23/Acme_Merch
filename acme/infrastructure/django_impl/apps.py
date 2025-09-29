from django.apps import AppConfig

class InfrastructureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'acme.infrastructure.django_impl'
    label = 'infrastructure'
