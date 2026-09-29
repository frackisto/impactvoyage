from django.utils import timezone

from .models import Notification


def notify_staff(event, title, message="", link="", related_object=None, details=(),
                 reply_to=()):
    """Prévient l'agence d'un événement sur tous les canaux actifs (STAFF_NOTIFICATION_CHANNELS)."""
    from .channels import StaffAlert, staff_channels

    alert = StaffAlert(event=event, title=title, message=message, link=link,
                       related_object=related_object, details=list(details),
                       reply_to=list(reply_to))
    for channel in staff_channels():
        channel.send(alert)


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
