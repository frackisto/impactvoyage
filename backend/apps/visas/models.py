from django.core.validators import MinValueValidator
from django.db import models

from apps.core.choices import Currency
from apps.core.models import PublishableMixin, TimeStampedModel


class VisaService(TimeStampedModel, PublishableMixin):
    """
    Accompagnement visa pour un pays de destination, une nationalité, un type
    et un motif donnés — CdC § 7, § 27. La page /visa/<country_slug> regroupe
    toutes les lignes d'un même pays.
    """

    class Purpose(models.TextChoices):
        TOURISME = "TOURISME", "Tourisme"
        AFFAIRES = "AFFAIRES", "Affaires"
        ETUDES = "ETUDES", "Études"
        FAMILLE = "FAMILLE", "Visite familiale"
        TRANSIT = "TRANSIT", "Transit"
        AUTRE = "AUTRE", "Autre"

    destination_country_code = models.CharField(
        "pays de destination (ISO 3166-1)", max_length=2, db_index=True
    )
    country_slug = models.SlugField("slug du pays", max_length=100, db_index=True)
    nationality_code = models.CharField(
        "nationalité (ISO 3166-1)", max_length=2, db_index=True
    )
    visa_type = models.CharField("type de visa", max_length=100)
    purpose = models.CharField("motif", max_length=10, choices=Purpose.choices)
    validity_duration = models.CharField("durée de validité", max_length=100, blank=True)
    processing_time = models.CharField("délai de traitement", max_length=100, blank=True)
    fees = models.DecimalField(
        "frais", max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.XOF)
    required_documents = models.TextField("documents requis", blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "service visa"
        verbose_name_plural = "services visa"
        ordering = ["country_slug", "visa_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["destination_country_code", "nationality_code", "visa_type", "purpose"],
                name="unique_visa_service",
            ),
        ]

    def __str__(self):
        return (
            f"Visa {self.destination_country_code} — {self.visa_type} "
            f"({self.nationality_code}, {self.get_purpose_display()})"
        )
