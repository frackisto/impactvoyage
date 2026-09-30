"""
Applique tout de suite les durées de conservation des données personnelles
(tâche Celery quotidienne apply_retention_task, voir apps/core/privacy.py).
"""
from django.core.management.base import BaseCommand

from apps.core.privacy import apply_retention


class Command(BaseCommand):
    help = "Supprime ou anonymise les données personnelles dont la durée de conservation est dépassée."

    def handle(self, *args, **options):
        report = apply_retention()
        if not report:
            self.stdout.write("Aucune donnée à supprimer ou anonymiser.")
        for label, count in report.items():
            self.stdout.write(f"{label} : {count}")
