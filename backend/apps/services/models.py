from django.db import models

from apps.core.choices import RequestedService
from apps.core.models import PublishableMixin, SlugMixin, TimeStampedModel


class Service(TimeStampedModel, SlugMixin, PublishableMixin):
    """Prestation présentée sur la page /services — CdC § 11."""

    title = models.CharField("titre", max_length=150)
    short_description = models.CharField("accroche", max_length=300, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField("icône (Lucide)", max_length=50, blank=True)
    order = models.PositiveSmallIntegerField("ordre", default=0)
    quote_service_type = models.CharField(
        "prestation pré-cochée dans le devis",
        max_length=20,
        choices=RequestedService.choices,
        blank=True,
    )

    class Meta:
        verbose_name = "service"
        ordering = ["order", "title"]

    def __str__(self):
        return self.title
