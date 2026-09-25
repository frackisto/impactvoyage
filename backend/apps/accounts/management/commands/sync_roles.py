from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.accounts.permissions_sync import assign_role_group, sync_role_groups
from apps.accounts.roles import group_name


class Command(BaseCommand):
    help = "Crée/met à jour un groupe de permissions par rôle et y range chaque utilisateur."

    def handle(self, *args, **options):
        summary = sync_role_groups()
        for role, count in summary.items():
            self.stdout.write(f"{group_name(role)} : {count} permission(s)")
        users = 0
        for user in User.objects.all():
            assign_role_group(user)
            users += 1
        self.stdout.write(self.style.SUCCESS(f"{users} utilisateur(s) rangé(s) dans leur groupe."))
