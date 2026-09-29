from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    """Notification du tableau de bord pour un membre du staff — CdC § 30."""

    class Event(models.TextChoices):
        QUOTE_CREATED = "QUOTE_CREATED", "Nouvelle demande de devis"
        QUOTE_ACCEPTED = "QUOTE_ACCEPTED", "Devis accepté par le client"
        QUOTE_DECLINED = "QUOTE_DECLINED", "Devis refusé par le client"
        BOOKING_REQUESTED = "BOOKING_REQUESTED", "Nouvelle demande de réservation"
        BOOKING_CANCELLED = "BOOKING_CANCELLED", "Réservation annulée"
        BOOKING_EXPIRED = "BOOKING_EXPIRED", "Réservation expirée"
        CONTACT_RECEIVED = "CONTACT_RECEIVED", "Nouveau message de contact"
        REVIEW_SUBMITTED = "REVIEW_SUBMITTED", "Nouvel avis à modérer"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    event = models.CharField("événement", max_length=20, choices=Event.choices)
    title = models.CharField("titre", max_length=200)
    message = models.TextField(blank=True)
    link = models.CharField("lien", max_length=500, blank=True)
    is_read = models.BooleanField("lue", default=False)
    read_at = models.DateTimeField("lue le", null=True, blank=True)

    # Seul lien générique toléré (architecture § 3.7) : aucune intégrité critique.
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    related_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return self.title
