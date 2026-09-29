"""
Canaux de notification de l'agence (architecture § 7.3, CdC § 30).

Chaque canal reçoit une StaffAlert (événement, titre, message, récapitulatif,
lien vers l'admin). Les canaux actifs sont listés dans le réglage
STAFF_NOTIFICATION_CHANNELS : ajouter WhatsApp ou SMS = ajouter la classe à la
liste et configurer un prestataire, sans toucher aux apps métier.
"""
import logging
from dataclasses import dataclass, field

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils.module_loading import import_string

from .emails import Email, send_email
from .models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()

# Rôles prévenus pour chaque type d'événement (les SUPER_ADMIN et ADMIN le sont toujours).
EVENT_ROLES = {
    Notification.Event.QUOTE_CREATED: {User.Role.COMMERCIAL},
    Notification.Event.QUOTE_ACCEPTED: {User.Role.COMMERCIAL},
    Notification.Event.QUOTE_DECLINED: {User.Role.COMMERCIAL},
    Notification.Event.BOOKING_REQUESTED: {User.Role.COMMERCIAL, User.Role.GESTIONNAIRE},
    Notification.Event.BOOKING_CANCELLED: {User.Role.COMMERCIAL, User.Role.GESTIONNAIRE},
    Notification.Event.BOOKING_EXPIRED: {User.Role.COMMERCIAL, User.Role.GESTIONNAIRE},
    Notification.Event.CONTACT_RECEIVED: {User.Role.COMMERCIAL},
    Notification.Event.REVIEW_SUBMITTED: {User.Role.GESTIONNAIRE},
}
ALWAYS_NOTIFIED = {User.Role.SUPER_ADMIN, User.Role.ADMIN}


@dataclass
class StaffAlert:
    event: str
    title: str
    message: str = ""
    link: str = ""  # chemin dans l'admin (/admin/…)
    related_object: object = None
    details: list = field(default_factory=list)  # [(libellé, valeur)]
    reply_to: list = field(default_factory=list)  # ex. l'adresse du client

    @property
    def admin_url(self):
        return f"{settings.BACKEND_URL}{self.link}" if self.link else ""


def recipients_for(event):
    roles = ALWAYS_NOTIFIED | EVENT_ROLES.get(event, set())
    return User.objects.filter(role__in=roles, is_active=True)


class Channel:
    def send(self, alert):
        raise NotImplementedError


class DashboardChannel(Channel):
    """Notification visible dans le backoffice de chaque membre de l'équipe concerné."""

    def send(self, alert):
        related = alert.related_object
        content_type = ContentType.objects.get_for_model(related) if related else None
        Notification.objects.bulk_create(
            Notification(
                recipient=user,
                event=alert.event,
                title=alert.title,
                message=alert.message,
                link=alert.link,
                content_type=content_type,
                object_id=related.pk if related else None,
            )
            for user in recipients_for(alert.event)
        )


class AgencyEmailChannel(Channel):
    """Email HTML à l'adresse de l'agence (AGENCY_NOTIFICATION_EMAIL), en français."""

    def send(self, alert):
        send_email(settings.AGENCY_NOTIFICATION_EMAIL, Email(
            subject=f"[Impact Voyage] {alert.title}",
            heading=alert.title,
            paragraphs=[alert.message] if alert.message else [],
            details=alert.details,
            action=("Ouvrir dans l'administration", alert.admin_url) if alert.link else None,
            reply_to=alert.reply_to,
            for_agency=True,
        ))


class ShortMessageChannel(Channel):
    """
    Message court (WhatsApp ou SMS) aux membres de l'équipe concernés qui ont
    renseigné leur numéro. Le prestataire est choisi par SHORT_MESSAGE_BACKEND ;
    l'envoi part par Celery après validation de la transaction.
    """

    channel = None  # "whatsapp" | "sms"
    number_field = None

    def text(self, alert):
        lines = [f"Impact Voyage — {alert.title}"]
        if alert.admin_url:
            lines.append(alert.admin_url)
        return "\n".join(lines)

    def send(self, alert):
        from .tasks import send_short_message_task

        numbers = {
            number for number in recipients_for(alert.event)
            .exclude(**{self.number_field: ""}).values_list(self.number_field, flat=True)
        }
        text = self.text(alert)
        backend = settings.SHORT_MESSAGE_BACKEND
        for number in sorted(numbers):
            transaction.on_commit(
                lambda number=number: send_short_message_task.delay(backend, self.channel, number, text)
            )


class WhatsAppChannel(ShortMessageChannel):
    channel = "whatsapp"
    number_field = "whatsapp"


class SmsChannel(ShortMessageChannel):
    channel = "sms"
    number_field = "phone"


# --- Prestataires de messages courts ------------------------------------------


class ConsoleBackend:
    """Prestataire de développement : écrit le message dans les journaux."""

    def send(self, channel, to, text):
        logger.info("[%s → %s] %s", channel, to, text)


def staff_channels():
    return [import_string(path)() for path in settings.STAFF_NOTIFICATION_CHANNELS]
