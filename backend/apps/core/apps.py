from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self):
        from . import checks  # noqa: F401 (enregistre les vérifications de démarrage)
        from .revalidation import connect_signals

        connect_signals()  # régénération des pages du site quand un contenu change
