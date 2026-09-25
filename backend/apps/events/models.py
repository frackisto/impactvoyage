from django.db import models
from django.db.models import F, Q

from apps.core.models import (
    CoverImageMixin,
    MediaAsset,
    PublishableMixin,
    SlugMixin,
    TimeStampedModel,
)


class Event(TimeStampedModel, SlugMixin, PublishableMixin, CoverImageMixin):
    """Événement ou activité réalisé par l'agence — CdC § 15."""

    UPLOAD_FOLDER = "events"

    class Category(models.TextChoices):
        VOYAGE_GROUPE = "VOYAGE_GROUPE", "Voyage de groupe"
        EXCURSION = "EXCURSION", "Excursion"
        PROFESSIONNEL = "PROFESSIONNEL", "Événement professionnel"
        CULTUREL = "CULTUREL", "Événement culturel"
        SPORTIF = "SPORTIF", "Événement sportif"
        TOURISTIQUE = "TOURISTIQUE", "Événement touristique"
        PRIVE = "PRIVE", "Événement privé"
        AUTRE = "AUTRE", "Autre"

    title = models.CharField("titre", max_length=200)
    short_description = models.CharField("accroche", max_length=300, blank=True)
    description = models.TextField()
    category = models.CharField(
        "catégorie", max_length=15, choices=Category.choices, db_index=True
    )
    date = models.DateField(db_index=True)
    end_date = models.DateField("date de fin", null=True, blank=True)
    location = models.CharField("lieu", max_length=200)
    destination = models.ForeignKey(
        "destinations.Destination",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    participants_count = models.PositiveIntegerField("participants", null=True, blank=True)
    partners = models.JSONField(
        "partenaires",
        default=list,
        blank=True,
        help_text='Ex. [{"name": "…", "logo": "https://…", "url": "https://…"}]',
    )
    is_featured = models.BooleanField("mise en avant", default=False, db_index=True)

    class Meta:
        verbose_name = "événement"
        ordering = ["-date"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__isnull=True) | Q(end_date__gte=F("date")),
                name="event_end_after_start",
            ),
        ]

    def __str__(self):
        return self.title


class EventImage(MediaAsset):
    """Photo ou vidéo de la galerie d'un événement."""

    UPLOAD_FOLDER = "events/galerie"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="media")

    class Meta(MediaAsset.Meta):
        verbose_name = "média d'événement"
