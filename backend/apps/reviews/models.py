from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.db import at_most_one
from apps.core.files import UploadTo
from apps.core.models import TimeStampedModel
from apps.core.validators import image_validators

REVIEW_TARGETS = ("destination", "tour", "hotel", "activity")


class Review(TimeStampedModel):
    """Avis client, publié après validation dans l'administration — CdC § 20."""

    UPLOAD_FOLDER = "reviews"

    class Status(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        APPROUVE = "APPROUVE", "Approuvé"
        REFUSE = "REFUSE", "Refusé"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviews",
    )
    author_name = models.CharField("nom", max_length=150)
    author_email = models.EmailField("email (non publié)")
    rating = models.PositiveSmallIntegerField("note")
    comment = models.TextField("commentaire")
    photo = models.ImageField(upload_to=UploadTo(), validators=image_validators, blank=True)

    destination = models.ForeignKey(
        "destinations.Destination", on_delete=models.CASCADE, null=True, blank=True,
        related_name="reviews",
    )
    tour = models.ForeignKey(
        "tours.Tour", on_delete=models.CASCADE, null=True, blank=True, related_name="reviews"
    )
    hotel = models.ForeignKey(
        "accommodations.Hotel", on_delete=models.CASCADE, null=True, blank=True,
        related_name="reviews",
    )
    activity = models.ForeignKey(
        "activities.Activity", on_delete=models.CASCADE, null=True, blank=True,
        related_name="reviews",
    )

    is_featured = models.BooleanField("afficher sur l'accueil", default=False)
    status = models.CharField(
        "statut", max_length=10, choices=Status.choices, default=Status.EN_ATTENTE, db_index=True
    )

    class Meta:
        verbose_name = "avis"
        verbose_name_plural = "avis"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(rating__gte=1, rating__lte=5), name="review_rating_1_to_5"
            ),
            models.CheckConstraint(
                condition=at_most_one(*REVIEW_TARGETS), name="review_at_most_one_target"
            ),
        ]

    def __str__(self):
        return f"{self.author_name} — {self.rating}/5"
