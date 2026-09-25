from django.db import models

from apps.core.models import (
    BookableMixin,
    Category,
    CoverImageMixin,
    GalleryImage,
    PublishableMixin,
    SlugMixin,
    TimeStampedModel,
)


class Activity(TimeStampedModel, SlugMixin, PublishableMixin, CoverImageMixin, BookableMixin):
    """Activité touristique (excursion, visite, sortie...) — CdC § 7."""

    UPLOAD_FOLDER = "activities"

    title = models.CharField("titre", max_length=200)
    short_description = models.CharField("accroche", max_length=300, blank=True)
    description = models.TextField()
    destination = models.ForeignKey(
        "destinations.Destination", on_delete=models.PROTECT, related_name="activities"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
        limit_choices_to={"kind": Category.Kind.ACTIVITY},
    )
    duration_hours = models.DecimalField("durée (heures)", max_digits=5, decimal_places=1)
    max_participants = models.PositiveSmallIntegerField(null=True, blank=True)
    is_featured = models.BooleanField("mise en avant", default=False, db_index=True)
    view_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = "activité"
        ordering = ["title"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_hours__gt=0), name="activity_duration_positive"
            ),
        ]

    def __str__(self):
        return self.title


class ActivityImage(GalleryImage):
    UPLOAD_FOLDER = "activities/galerie"

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="images")
