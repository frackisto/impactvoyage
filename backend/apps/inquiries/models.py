import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.core.choices import Currency, RequestedService
from apps.core.models import ReferenceMixin, SoftDeleteModel, TimeStampedModel


class QuoteRequest(ReferenceMixin, TimeStampedModel, SoftDeleteModel):
    """Demande de devis / voyage personnalisé — CdC § 18, § 38."""

    REFERENCE_PREFIX = "DV"

    class Status(models.TextChoices):
        NOUVELLE = "NOUVELLE", "Nouvelle"
        EN_COURS = "EN_COURS", "En cours"
        DEVIS_ENVOYE = "DEVIS_ENVOYE", "Devis envoyé"
        ACCEPTEE = "ACCEPTEE", "Acceptée"
        REFUSEE = "REFUSEE", "Refusée"
        TERMINEE = "TERMINEE", "Terminée"

    class TravelType(models.TextChoices):
        LOISIRS = "LOISIRS", "Loisirs"
        AFFAIRES = "AFFAIRES", "Affaires"
        FAMILLE = "FAMILLE", "Famille"
        LUNE_DE_MIEL = "LUNE_DE_MIEL", "Lune de miel"
        GROUPE = "GROUPE", "Groupe"
        PELERINAGE = "PELERINAGE", "Pèlerinage"
        ETUDES = "ETUDES", "Études"
        AUTRE = "AUTRE", "Autre"

    # Secret du lien envoyé au client pour consulter et valider la proposition
    # sans compte (/devis/<reference>?token=...). Jamais exposé dans les listes.
    access_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    first_name = models.CharField("prénom", max_length=100)
    last_name = models.CharField("nom", max_length=100)
    email = models.EmailField()
    phone = models.CharField("téléphone", max_length=30)
    whatsapp = models.CharField(max_length=30, blank=True)
    country_code = models.CharField("pays de résidence (ISO 3166-1)", max_length=2, blank=True)

    destination_text = models.CharField("destination souhaitée", max_length=200, blank=True)
    destination = models.ForeignKey(
        "destinations.Destination",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quote_requests",
    )
    date_departure = models.DateField("date de départ", null=True, blank=True)
    date_return = models.DateField("date de retour", null=True, blank=True)
    adults = models.PositiveSmallIntegerField("adultes", default=1, validators=[MinValueValidator(1)])
    children = models.PositiveSmallIntegerField("enfants", default=0)
    travel_type = models.CharField(
        "type de voyage", max_length=15, choices=TravelType.choices, blank=True
    )
    budget = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.XOF)
    accommodation_pref = models.CharField("hébergement souhaité", max_length=200, blank=True)
    transport_pref = models.CharField("transport", max_length=200, blank=True)
    activities = models.ManyToManyField(
        "activities.Activity", blank=True, related_name="quote_requests"
    )
    services_requested = ArrayField(
        models.CharField(max_length=20, choices=RequestedService.choices),
        verbose_name="services demandés",
        default=list,
        blank=True,
    )
    comments = models.TextField("commentaires", blank=True)

    source_tour = models.ForeignKey(
        "tours.Tour", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    source_offer = models.ForeignKey(
        "offers.Offer", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_quotes",
        limit_choices_to={"is_staff": True},
        verbose_name="commercial assigné",
    )
    proposal_amount = models.DecimalField(
        "montant proposé", max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
    )
    proposal_message = models.TextField("proposition", blank=True)
    proposal_sent_at = models.DateTimeField("proposition envoyée le", null=True, blank=True)
    proposal_valid_until = models.DateField("proposition valable jusqu'au", null=True, blank=True)

    language = models.CharField("langue", max_length=5, default="fr")
    consent_at = models.DateTimeField("consentement donné le", null=True, blank=True)
    status = models.CharField(
        "statut", max_length=15, choices=Status.choices, default=Status.NOUVELLE, db_index=True
    )

    class Meta:
        verbose_name = "demande de devis"
        verbose_name_plural = "demandes de devis"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"])]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(date_departure__isnull=True)
                    | Q(date_return__isnull=True)
                    | Q(date_return__gte=F("date_departure"))
                ),
                name="quote_return_after_departure",
            ),
            models.CheckConstraint(condition=Q(adults__gte=1), name="quote_at_least_one_adult"),
        ]

    def __str__(self):
        return f"{self.reference} — {self.first_name} {self.last_name}"


class ContactMessage(TimeStampedModel):
    """Message du formulaire de contact — CdC § 19."""

    class Status(models.TextChoices):
        NOUVEAU = "NOUVEAU", "Nouveau"
        LU = "LU", "Lu"
        TRAITE = "TRAITE", "Traité"
        ARCHIVE = "ARCHIVE", "Archivé"

    name = models.CharField("nom", max_length=150)
    email = models.EmailField()
    phone = models.CharField("téléphone", max_length=30, blank=True)
    subject = models.CharField("objet", max_length=200)
    message = models.TextField()
    status = models.CharField(
        "statut", max_length=10, choices=Status.choices, default=Status.NOUVEAU, db_index=True
    )

    class Meta:
        verbose_name = "message de contact"
        verbose_name_plural = "messages de contact"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.subject}"
