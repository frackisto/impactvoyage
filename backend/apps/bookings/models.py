import uuid

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeBoundary, RangeOperators
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.core.choices import Currency
from apps.core.db import DateRange, exactly_one
from apps.core.models import ReferenceMixin, SoftDeleteModel, TimeStampedModel

BOOKING_TARGETS = ("tour_departure", "room", "residence", "vehicle", "activity")


class Booking(ReferenceMixin, TimeStampedModel, SoftDeleteModel):
    """
    Demande de réservation ou réservation (architecture § 3.8).
    Les transitions de statut passent exclusivement par bookings/services.py.
    """

    REFERENCE_PREFIX = "IV"

    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Demande reçue"
        PENDING = "PENDING", "En attente de confirmation"
        CONFIRMED = "CONFIRMED", "Confirmée"
        COMPLETED = "COMPLETED", "Terminée"
        CANCELLED = "CANCELLED", "Annulée"
        REJECTED = "REJECTED", "Refusée"
        EXPIRED = "EXPIRED", "Expirée"

    # Statuts qui bloquent le stock (places, véhicule) : voir BookingItem.is_blocking.
    BLOCKING_STATUSES = frozenset({Status.PENDING, Status.CONFIRMED})

    # Secret du lien de suivi envoyé au client (/reservation/<reference>?token=...) :
    # consultation et annulation sans compte. Jamais exposé dans les listes.
    access_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    contact_name = models.CharField("nom du contact", max_length=200)
    contact_email = models.EmailField("email du contact")
    contact_phone = models.CharField("téléphone du contact", max_length=30)
    quote = models.OneToOneField(
        "inquiries.QuoteRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking",
        verbose_name="devis d'origine",
    )
    status = models.CharField(
        "statut", max_length=10, choices=Status.choices, default=Status.REQUESTED, db_index=True
    )
    expires_at = models.DateTimeField("expire le", null=True, blank=True)
    customer_comments = models.TextField("commentaires du client", blank=True)
    internal_notes = models.TextField("notes internes", blank=True)
    total_amount = models.DecimalField(
        "montant total", max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.XOF)
    language = models.CharField("langue", max_length=5, default="fr")
    consent_at = models.DateTimeField("consentement au traitement des données", null=True, blank=True)

    class Meta:
        verbose_name = "réservation"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(
                fields=["expires_at"],
                condition=Q(status="PENDING"),
                name="booking_pending_expiry_idx",
            ),
        ]

    def __str__(self):
        return f"{self.reference} — {self.contact_name}"


class BookingItem(TimeStampedModel):
    """
    Ligne de réservation : une offre, des dates, un prix figé.
    is_blocking est dénormalisé depuis le statut du Booking parent pour que
    PostgreSQL puisse interdire les chevauchements de location de véhicules.
    """

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="items")

    tour_departure = models.ForeignKey(
        "tours.TourDeparture", on_delete=models.PROTECT, null=True, blank=True,
        related_name="booking_items",
    )
    room = models.ForeignKey(
        "accommodations.Room", on_delete=models.PROTECT, null=True, blank=True,
        related_name="booking_items",
    )
    residence = models.ForeignKey(
        "accommodations.Residence", on_delete=models.PROTECT, null=True, blank=True,
        related_name="booking_items",
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle", on_delete=models.PROTECT, null=True, blank=True,
        related_name="booking_items",
    )
    activity = models.ForeignKey(
        "activities.Activity", on_delete=models.PROTECT, null=True, blank=True,
        related_name="booking_items",
    )

    label = models.CharField("libellé", max_length=255)
    unit_price = models.DecimalField(
        "prix unitaire", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    quantity = models.PositiveIntegerField("quantité", default=1, validators=[MinValueValidator(1)])
    line_total = models.DecimalField(
        "total ligne", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    # end_date exclusive : jour de restitution du véhicule / de départ de l'hébergement.
    start_date = models.DateField("début")
    end_date = models.DateField("fin (exclue)")
    pickup_location = models.CharField("lieu de prise en charge", max_length=200, blank=True)
    dropoff_location = models.CharField("lieu de restitution", max_length=200, blank=True)
    is_blocking = models.BooleanField("bloque le stock", default=False, editable=False)

    class Meta:
        verbose_name = "ligne de réservation"
        verbose_name_plural = "lignes de réservation"
        ordering = ["booking", "start_date"]
        constraints = [
            models.CheckConstraint(
                condition=exactly_one(*BOOKING_TARGETS), name="bookingitem_exactly_one_target"
            ),
            models.CheckConstraint(
                condition=Q(end_date__gt=F("start_date")), name="bookingitem_end_after_start"
            ),
            models.CheckConstraint(condition=Q(quantity__gte=1), name="bookingitem_quantity_min_1"),
            ExclusionConstraint(
                name="bookingitem_vehicle_no_overlap",
                expressions=[
                    ("vehicle", RangeOperators.EQUAL),
                    (DateRange("start_date", "end_date", RangeBoundary()), RangeOperators.OVERLAPS),
                ],
                condition=Q(is_blocking=True, vehicle__isnull=False),
            ),
        ]

    def __str__(self):
        return f"{self.booking.reference} — {self.label}"
