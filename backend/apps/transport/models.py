from django.core.validators import MinValueValidator
from django.db import models

from apps.core.choices import Currency
from apps.core.models import CoverImageMixin, PublishableMixin, SlugMixin, TimeStampedModel


class TransportService(TimeStampedModel, SlugMixin, PublishableMixin, CoverImageMixin):
    """
    Service de transport (hors location de véhicules) — CdC § 7.
    Les demandes (date, voyageurs) passent par un devis.
    """

    UPLOAD_FOLDER = "transport"

    class TransportType(models.TextChoices):
        TRANSFERT_AEROPORT = "TRANSFERT_AEROPORT", "Transfert aéroport"
        BUS = "BUS", "Bus"
        NAVETTE = "NAVETTE", "Navette"
        FERRY = "FERRY", "Bateau / ferry"
        TRAIN = "TRAIN", "Train"
        CHAUFFEUR = "CHAUFFEUR", "Véhicule avec chauffeur"

    title = models.CharField("titre", max_length=200)
    description = models.TextField(blank=True)
    transport_type = models.CharField(
        "type de transport", max_length=20, choices=TransportType.choices, db_index=True
    )
    origin = models.CharField("origine", max_length=150)
    destination = models.CharField(max_length=150)
    max_passengers = models.PositiveSmallIntegerField("passagers maximum", null=True, blank=True)
    price_from = models.DecimalField(
        "prix à partir de", max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.XOF)
    schedule_info = models.TextField("horaires / fréquence", blank=True)

    class Meta:
        verbose_name = "service de transport"
        verbose_name_plural = "services de transport"
        ordering = ["transport_type", "origin"]

    def __str__(self):
        return f"{self.title} ({self.origin} → {self.destination})"
