from django.utils import timezone

from .models import Notification


def notify_staff(event, title, message="", link="", related_object=None):
    """Prévient l'agence d'un événement sur tous les canaux actifs."""
    from .channels import STAFF_CHANNELS

    for channel in STAFF_CHANNELS:
        channel.send(event, title, message, link, related_object)


def mark_as_read(notification):
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at", "updated_at"])
    return notification


def mark_all_as_read(user):
    return Notification.objects.filter(recipient=user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )


def admin_path(obj):
    """Chemin de la fiche d'un objet dans l'admin Django (lien des notifications)."""
    return f"/admin/{obj._meta.app_label}/{obj._meta.model_name}/{obj.pk}/change/"
