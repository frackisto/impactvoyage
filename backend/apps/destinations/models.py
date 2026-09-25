from django.db import models

from apps.core.models import (
    CoverImageMixin,
    GalleryImage,
    PublishableMixin,
    SlugMixin,
    Tag,
    TimeStampedModel,
)


class Destination(TimeStampedModel, SlugMixin, PublishableMixin, CoverImageMixin):
    """Destination touristique (pays, région ou ville) — CdC § 8."""

    UPLOAD_FOLDER = "destinations"

    class Continent(models.TextChoices):
        AFRIQUE = "AFRIQUE", "Afrique"
        EUROPE = "EUROPE", "Europe"
        AMERIQUES = "AMERIQUES", "Amériques"
        ASIE = "ASIE", "Asie"
        MOYEN_ORIENT = "MOYEN_ORIENT", "Moyen-Orient"
        OCEANIE = "OCEANIE", "Océanie"

    name = models.CharField("nom", max_length=150)
    continent = models.CharField(max_length=20, choices=Continent.choices, db_index=True)
    # Le nom du pays est affiché par le frontend (Intl.DisplayNames) dans la
    # langue du visiteur : on ne stocke que le code ISO.
    country_code = models.CharField("pays (ISO 3166-1)", max_length=2, db_index=True)
    city = models.CharField("ville", max_length=100, blank=True)
    short_description = models.CharField("accroche", max_length=300, blank=True)
    description = models.TextField()
    best_period = models.CharField("meilleure période", max_length=200, blank=True)
    attractions = models.TextField(blank=True, help_text="Une attraction par ligne.")
    tips = models.TextField("conseils", blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="destinations")
    is_featured = models.BooleanField("mise en avant", default=False, db_index=True)
    view_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DestinationImage(GalleryImage):
    UPLOAD_FOLDER = "destinations/galerie"

    destination = models.ForeignKey(
        Destination, on_delete=models.CASCADE, related_name="images"
    )
