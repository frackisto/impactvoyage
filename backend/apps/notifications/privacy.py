"""
Notifications de l'équipe (apps/core/privacy.py) : leur texte reprend le nom et le
message du client. Supprimées avec les données effacées et après leur durée de conservation.
"""
from django.contrib.contenttypes.models import ContentType

from apps.core import privacy

from .models import Notification


@privacy.register_cleanup
def delete_related_notifications(erased):
    for model, pk in erased:
        Notification.objects.filter(
            content_type=ContentType.objects.get_for_model(model), object_id=pk
        ).delete()


@privacy.register
class Notifications(privacy.PersonalDataSource):
    label = "Notifications de l'équipe"

    def find(self, email):
        return Notification.objects.none()

    def apply_retention(self, now):
        cutoff = privacy.retention_cutoff("notifications", now)
        deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
        return deleted
