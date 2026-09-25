from decimal import ROUND_HALF_UP, Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.core.choices import Currency
from apps.core.db import at_most_one
from apps.core.models import CoverImageMixin, SlugMixin, TimeStampedModel

OFFER_TARGETS = ("tour", "hotel", "residence", "vehicle", "activity")


class OfferQuerySet(models.QuerySet):
    def currently_active(self):
        today = timezone.localdate()
        return self.filter(is_active=True, start_date__lte=today, end_date__gte=today)


class Offer(TimeStampedModel, SlugMixin, CoverImageMixin):
    """Offre promotionnelle datée — CdC § 17."""

    UPLOAD_FOLDER = "offers"

    class OfferType(models.TextChoices):
        VOYAGE = "VOYAGE", "Voyage"
        HOTEL = "HOTEL", "Hôtel"
        CIRCUIT = "CIRCUIT", "Circuit"
        BILLET = "BILLET", "Billet d'avion"
        LOCATION = "LOCATION", "Location"
        PACKAGE = "PACKAGE", "Package"

    class Badge(models.TextChoices):
        NOUVEAU = "NOUVEAU", "Nouveau"
        PROMOTION = "PROMOTION", "Promotion"
        POPULAIRE = "POPULAIRE", "Populaire"
        DERNIERES_PLACES = "DERNIERES_PLACES", "Dernières places"

    title = models.CharField("titre", max_length=200)
    short_description = models.CharField("accroche", max_length=300, blank=True)
    description = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    offer_type = models.CharField("type", max_length=10, choices=OfferType.choices, db_index=True)
    initial_price = models.DecimalField(
        "prix initial", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    promo_price = models.DecimalField(
        "prix promotionnel", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.XOF)
    start_date = models.DateField("début")
    end_date = models.DateField("fin")
    seats_available = models.PositiveIntegerField("places disponibles", null=True, blank=True)
    badge = models.CharField(max_length=20, choices=Badge.choices, blank=True)
    destination = models.ForeignKey(
        "destinations.Destination",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="offers",
    )
    is_active = models.BooleanField("active", default=True, db_index=True)

    # Cible optionnelle (aucune pour un billet ou un package) : au plus une.
    tour = models.ForeignKey(
        "tours.Tour", on_delete=models.CASCADE, null=True, blank=True, related_name="offers"
    )
    hotel = models.ForeignKey(
        "accommodations.Hotel", on_delete=models.CASCADE, null=True, blank=True,
        related_name="offers",
    )
    residence = models.ForeignKey(
        "accommodations.Residence", on_delete=models.CASCADE, null=True, blank=True,
        related_name="offers",
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle", on_delete=models.CASCADE, null=True, blank=True,
        related_name="offers",
    )
    activity = models.ForeignKey(
        "activities.Activity", on_delete=models.CASCADE, null=True, blank=True,
        related_name="offers",
    )

    objects = OfferQuerySet.as_manager()

    class Meta:
        verbose_name = "offre"
        ordering = ["end_date"]
        indexes = [models.Index(fields=["start_date", "end_date"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(promo_price__lt=F("initial_price")), name="offer_promo_below_initial"
            ),
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")), name="offer_end_after_start"
            ),
            models.CheckConstraint(
                condition=at_most_one(*OFFER_TARGETS), name="offer_at_most_one_target"
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def discount_percent(self):
        """Pourcentage de réduction, calculé (jamais saisi)."""
        if not self.initial_price:
            return 0
        ratio = (self.initial_price - self.promo_price) / self.initial_price * 100
        return int(Decimal(ratio).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @property
    def target(self):
        for name in OFFER_TARGETS:
            obj = getattr(self, name)
            if obj is not None:
                return obj
        return None
