from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.core.models import (
    BookableMixin,
    Category,
    CoverImageMixin,
    GalleryImage,
    PublishableMixin,
    SlugMixin,
    TimeStampedModel,
)


class Tour(TimeStampedModel, SlugMixin, PublishableMixin, CoverImageMixin, BookableMixin):
    """Circuit national ou international — CdC § 9, § 10."""

    UPLOAD_FOLDER = "tours"

    class Scope(models.TextChoices):
        NATIONAL = "NATIONAL", "National"
        INTERNATIONAL = "INTERNATIONAL", "International"

    title = models.CharField("titre", max_length=200)
    short_description = models.CharField("accroche", max_length=300, blank=True)
    description = models.TextField()
    destination = models.ForeignKey(
        "destinations.Destination", on_delete=models.PROTECT, related_name="tours"
    )
    scope = models.CharField("portée", max_length=15, choices=Scope.choices, db_index=True)
    theme = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tours",
        limit_choices_to={"kind": Category.Kind.TOUR_THEME},
    )
    is_custom = models.BooleanField("circuit sur mesure", default=False)
    duration_days = models.PositiveSmallIntegerField(
        "durée (jours)", validators=[MinValueValidator(1)]
    )
    min_travelers = models.PositiveSmallIntegerField("voyageurs minimum", default=1)
    max_travelers = models.PositiveSmallIntegerField("voyageurs maximum", null=True, blank=True)
    departure_points = models.TextField("points de départ", blank=True)
    transport_info = models.TextField("transport", blank=True)
    accommodation_info = models.TextField("hébergement", blank=True)
    inclusions = models.TextField(blank=True)
    exclusions = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    activities = models.ManyToManyField(
        "activities.Activity", blank=True, related_name="tours"
    )
    is_featured = models.BooleanField("mise en avant", default=False, db_index=True)
    view_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = "circuit"
        ordering = ["title"]
        constraints = [
            models.CheckConstraint(
                condition=Q(duration_days__gte=1), name="tour_duration_positive"
            ),
            models.CheckConstraint(
                condition=Q(max_travelers__isnull=True) | Q(max_travelers__gte=F("min_travelers")),
                name="tour_max_travelers_gte_min",
            ),
        ]

    def __str__(self):
        return self.title


class TourImage(GalleryImage):
    UPLOAD_FOLDER = "tours/galerie"

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="images")


class TourDay(models.Model):
    """Programme jour par jour."""

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="days")
    day_number = models.PositiveSmallIntegerField("jour", validators=[MinValueValidator(1)])
    title = models.CharField("titre", max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "jour de programme"
        ordering = ["tour", "day_number"]
        constraints = [
            models.UniqueConstraint(fields=["tour", "day_number"], name="unique_tour_day"),
        ]

    def __str__(self):
        return f"Jour {self.day_number} — {self.title}"


class TourDeparture(TimeStampedModel):
    """
    Date de départ réservable d'un circuit, avec sa propre capacité.
    Supprimer un circuit supprime ses départs, sauf si l'un d'eux est référencé
    par une réservation (BookingItem, on_delete=PROTECT).
    """

    class Status(models.TextChoices):
        OPEN = "OPEN", "Ouvert"
        FULL = "FULL", "Complet"
        CANCELLED = "CANCELLED", "Annulé"

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="departures")
    start_date = models.DateField("date de départ")
    end_date = models.DateField("date de retour")
    capacity = models.PositiveIntegerField("places", validators=[MinValueValidator(1)])
    seats_reserved = models.PositiveIntegerField("places réservées", default=0)
    price_override = models.DecimalField(
        "prix spécifique",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    class Meta:
        verbose_name = "départ"
        ordering = ["start_date"]
        indexes = [models.Index(fields=["start_date", "status"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(seats_reserved__lte=F("capacity")), name="departure_not_overbooked"
            ),
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")), name="departure_end_after_start"
            ),
            models.UniqueConstraint(
                fields=["tour", "start_date"], name="unique_departure_per_day"
            ),
        ]

    def __str__(self):
        return f"{self.tour} — {self.start_date:%d/%m/%Y}"

    @property
    def seats_left(self):
        return self.capacity - self.seats_reserved

    @property
    def price(self):
        return self.price_override if self.price_override is not None else self.tour.base_price
