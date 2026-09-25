from django.apps import AppConfig, apps
from django.db.models.signals import post_migrate, post_save


def _sync_after_migrate(sender, app_config=None, **kwargs):
    # post_migrate est émis pour chaque app : on attend la dernière, quand les
    # permissions de tous les modèles existent.
    if app_config is list(apps.get_app_configs())[-1]:
        from .permissions_sync import sync_role_groups

        sync_role_groups()


def _assign_group(sender, instance, raw=False, **kwargs):
    if not raw:
        from .permissions_sync import assign_role_group

        assign_role_group(instance)


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Comptes utilisateurs, rôles et authentification"

    def ready(self):
        post_migrate.connect(_sync_after_migrate, dispatch_uid="accounts_sync_roles")
        post_save.connect(
            _assign_group, sender="accounts.User", dispatch_uid="accounts_assign_role_group"
        )
