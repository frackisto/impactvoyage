from django.db import models
from django.utils import timezone

from apps.core.files import UploadTo
from apps.core.models import (
    Category,
    MediaAsset,
    PublishableMixin,
    SlugMixin,
    TimeStampedModel,
)
from apps.core.validators import image_validators


class MediaAlbum(TimeStampedModel, SlugMixin, PublishableMixin):
    """Album de la médiathèque — CdC § 16."""

    UPLOAD_FOLDER = "mediatheque"

    title = models.CharField("titre", max_length=200)
    description = models.TextField(blank=True)
    cover = models.ImageField(
        "couverture", upload_to=UploadTo(), validators=image_validators, blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="media_albums",
        limit_choices_to={"kind": Category.Kind.MEDIA},
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="albums",
    )
    tour = models.ForeignKey(
        "tours.Tour",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="albums",
    )
    published_at = models.DateField("date de publication", default=timezone.localdate)

    class Meta:
        verbose_name = "album"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class MediaItem(MediaAsset):
    UPLOAD_FOLDER = "mediatheque"

    album = models.ForeignKey(MediaAlbum, on_delete=models.CASCADE, related_name="items")
    title = models.CharField("légende", max_length=200, blank=True)
    is_featured = models.BooleanField("mise en avant", default=False)

    class Meta(MediaAsset.Meta):
        verbose_name = "média"
