from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import (
    BookableMixin,
    CoverImageMixin,
    GalleryImage,
    PublishableMixin,
    SlugMixin,
    TimeStampedModel,
)


class Vehicle(TimeStampedModel, SlugMixin, PublishableMixin, CoverImageMixin, BookableMixin):
    """
    Véhicule de location ; une ligne = un véhicule physique, base_price = prix
    par jour — CdC § 12. La disponibilité se calcule à partir des BookingItem.
    """

    UPLOAD_FOLDER = "vehicles"

    class Category(models.TextChoices):
        ECONOMIQUE = "ECONOMIQUE", "Économique"
        BERLINE = "BERLINE", "Berline"
        SUV = "SUV", "SUV"
        QUATRE_QUATRE = "4X4", "4x4"
        MINIBUS = "MINIBUS", "Minibus"
        LUXE = "LUXE", "Luxe"
        UTILITAIRE = "UTILITAIRE", "Utilitaire"

    class Transmission(models.TextChoices):
        MANUELLE = "MANUELLE", "Manuelle"
        AUTOMATIQUE = "AUTOMATIQUE", "Automatique"

    class Fuel(models.TextChoices):
        ESSENCE = "ESSENCE", "Essence"
        DIESEL = "DIESEL", "Diesel"
        HYBRIDE = "HYBRIDE", "Hybride"
        ELECTRIQUE = "ELECTRIQUE", "Électrique"

    brand = models.CharField("marque", max_length=60)
    model = models.CharField("modèle", max_length=60)
    category = models.CharField(
        "catégorie", max_length=12, choices=Category.choices, db_index=True
    )
    year = models.PositiveSmallIntegerField("année", validators=[MinValueValidator(1990)])
    plate_number = models.CharField("immatriculation", max_length=20, unique=True)
    seats = models.PositiveSmallIntegerField("places", validators=[MinValueValidator(1)])
    transmission = models.CharField("boîte", max_length=12, choices=Transmission.choices)
    fuel = models.CharField("carburant", max_length=10, choices=Fuel.choices)
    air_conditioning = models.BooleanField("climatisation", default=True)
    features = models.JSONField(
        "caractéristiques", default=list, blank=True, help_text='Ex. ["GPS", "Bluetooth"]'
    )
    description = models.TextField(blank=True)
    is_featured = models.BooleanField("mise en avant", default=False, db_index=True)
    view_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = "véhicule"
        ordering = ["brand", "model"]

    def __str__(self):
        return f"{self.brand} {self.model} ({self.plate_number})"


class VehicleImage(GalleryImage):
    UPLOAD_FOLDER = "vehicles/galerie"

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="images")
