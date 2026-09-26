from django.db import models

from django.core.validators import MinValueValidator

from apps.core.choices import Currency, RequestedService
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


class ServicePrice(models.Model):
    """
    Tarif affiché d'une prestation (ex. « Prise de rendez-vous France : 20 000 F CFA »,
    « Assurance voyage 1 semaine : 14 000 F CFA »), modifiable dans l'admin.
    """

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="prices")
    label = models.CharField("libellé", max_length=150)
    price = models.DecimalField(
        "prix", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.XOF)
    unit = models.CharField("unité", max_length=50, blank=True, help_text="Ex. « par personne »")
    order = models.PositiveSmallIntegerField("ordre", default=0)

    class Meta:
        verbose_name = "tarif"
        ordering = ["service", "order", "id"]

    def __str__(self):
        return f"{self.label} — {self.price} {self.currency}"
