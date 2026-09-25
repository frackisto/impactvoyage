"""
Canaux de notification de l'agence (architecture § 7.3). Ajouter WhatsApp ou
SMS = écrire une classe Channel et l'ajouter à STAFF_CHANNELS, sans toucher
aux apps métier.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from .emails import send_email
from .models import Notification

User = get_user_model()

# Rôles prévenus pour chaque type d'événement (les SUPER_ADMIN et ADMIN le sont toujours).
EVENT_ROLES = {
    Notification.Event.QUOTE_CREATED: {User.Role.COMMERCIAL},
    Notification.Event.QUOTE_ACCEPTED: {User.Role.COMMERCIAL},
    Notification.Event.BOOKING_REQUESTED: {User.Role.COMMERCIAL, User.Role.GESTIONNAIRE},
    Notification.Event.BOOKING_CANCELLED: {User.Role.COMMERCIAL, User.Role.GESTIONNAIRE},
    Notification.Event.CONTACT_RECEIVED: {User.Role.COMMERCIAL},
    Notification.Event.REVIEW_SUBMITTED: {User.Role.GESTIONNAIRE},
}
ALWAYS_NOTIFIED = {User.Role.SUPER_ADMIN, User.Role.ADMIN}


class Channel:
    def send(self, event, title, message, link, related_object):
        raise NotImplementedError


class DashboardChannel(Channel):
    """Notification visible dans le tableau de bord de chaque membre du staff concerné."""

    def send(self, event, title, message, link, related_object):
        roles = ALWAYS_NOTIFIED | EVENT_ROLES.get(event, set())
        recipients = User.objects.filter(role__in=roles, is_active=True)
        content_type = (
            ContentType.objects.get_for_model(related_object) if related_object else None
        )
        Notification.objects.bulk_create(
            Notification(
                recipient=user,
                event=event,
                title=title,
                message=message,
                link=link,
                content_type=content_type,
                object_id=related_object.pk if related_object else None,
            )
            for user in recipients
        )


class AgencyEmailChannel(Channel):
    """Email à l'adresse de l'agence (AGENCY_NOTIFICATION_EMAIL)."""

    def send(self, event, title, message, link, related_object):
        body = message
        if link:
            body += f"\n\nVoir dans l'administration : {settings.BACKEND_URL}{link}"
        send_email(settings.AGENCY_NOTIFICATION_EMAIL, f"[Impact Voyage] {title}", body)


STAFF_CHANNELS = [DashboardChannel(), AgencyEmailChannel()]
