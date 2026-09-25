from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import (
    BookableMixin,
    CoverImageMixin,
    GalleryImage,
    PublishableMixin,
    SlugMixin,
    TimeStampedModel,
)


class Amenity(models.Model):
    """Équipement (Wi-Fi, piscine, climatisation...) — CdC § 13, § 14."""

    class Scope(models.TextChoices):
        HOTEL = "HOTEL", "Hôtels"
        RESIDENCE = "RESIDENCE", "Résidences"
        BOTH = "BOTH", "Les deux"

    name = models.CharField("nom", max_length=100, unique=True)
    icon = models.CharField("icône (Lucide)", max_length=50, blank=True)
    scope = models.CharField(max_length=10, choices=Scope.choices, default=Scope.BOTH)

    class Meta:
        verbose_name = "équipement"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Hotel(TimeStampedModel, SlugMixin, PublishableMixin, CoverImageMixin):
    """Hôtel, appartement ou hébergement partenaire — CdC § 14."""

    UPLOAD_FOLDER = "hotels"

    class AccommodationType(models.TextChoices):
        HOTEL = "HOTEL", "Hôtel"
        APARTMENT = "APARTMENT", "Appartement"
        PARTNER = "PARTNER", "Hébergement partenaire"

    name = models.CharField("nom", max_length=200)
    short_description = models.CharField("accroche", max_length=300, blank=True)
    description = models.TextField()
    destination = models.ForeignKey(
        "destinations.Destination", on_delete=models.PROTECT, related_name="hotels"
    )
    address = models.CharField("adresse", max_length=255, blank=True)
    accommodation_type = models.CharField(
        "type", max_length=10, choices=AccommodationType.choices, default=AccommodationType.HOTEL
    )
    stars = models.PositiveSmallIntegerField("étoiles", null=True, blank=True)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="hotels")
    is_featured = models.BooleanField("mise en avant", default=False, db_index=True)
    view_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = "hôtel"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(stars__isnull=True) | Q(stars__gte=1, stars__lte=5),
                name="hotel_stars_1_to_5",
            ),
        ]

    def __str__(self):
        return self.name


class HotelImage(GalleryImage):
    UPLOAD_FOLDER = "hotels/galerie"

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="images")


class Room(TimeStampedModel, BookableMixin):
    """Type de chambre d'un hôtel ; base_price = prix par nuit."""

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField("type de chambre", max_length=150)
    description = models.TextField(blank=True)
    capacity = models.PositiveSmallIntegerField("capacité", validators=[MinValueValidator(1)])
    quantity = models.PositiveSmallIntegerField("nombre de chambres", default=1)
    is_active = models.BooleanField("active", default=True)

    class Meta:
        verbose_name = "chambre"
        ordering = ["hotel", "base_price"]

    def __str__(self):
        return f"{self.hotel} — {self.name}"


class Residence(TimeStampedModel, SlugMixin, PublishableMixin, CoverImageMixin, BookableMixin):
    """Résidence meublée ; base_price = prix par nuit — CdC § 13."""

    UPLOAD_FOLDER = "residences"

    name = models.CharField("nom", max_length=200)
    short_description = models.CharField("accroche", max_length=300, blank=True)
    description = models.TextField()
    destination = models.ForeignKey(
        "destinations.Destination", on_delete=models.PROTECT, related_name="residences"
    )
    address = models.CharField("adresse", max_length=255, blank=True)
    rooms_count = models.PositiveSmallIntegerField(
        "nombre de chambres", validators=[MinValueValidator(1)]
    )
    capacity = models.PositiveSmallIntegerField("capacité", validators=[MinValueValidator(1)])
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="residences")
    services = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    is_featured = models.BooleanField("mise en avant", default=False, db_index=True)
    view_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = "résidence"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ResidenceImage(GalleryImage):
    UPLOAD_FOLDER = "residences/galerie"

    residence = models.ForeignKey(Residence, on_delete=models.CASCADE, related_name="images")
