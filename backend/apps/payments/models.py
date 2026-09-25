"""
Paiement — préparation future (CdC § 37). Modèles créés dès la Phase 3,
non branchés à un flux de paiement en V1. Chaque prestataire sera un adapter
(payments/providers/<nom>.py) derrière une interface commune.
"""
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.choices import Currency
from apps.core.models import TimeStampedModel


class PaymentMethod(models.TextChoices):
    MOBILE_MONEY = "MOBILE_MONEY", "Mobile Money"
    ORANGE_MONEY = "ORANGE_MONEY", "Orange Money"
    MTN_MOMO = "MTN_MOMO", "MTN MoMo"
    WAVE = "WAVE", "Wave"
    CARTE = "CARTE", "Carte bancaire"
    STRIPE = "STRIPE", "Stripe"
    AGENCE = "AGENCE", "Paiement à l'agence"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    PAID = "PAID", "Payé"
    FAILED = "FAILED", "Échoué"
    REFUNDED = "REFUNDED", "Remboursé"


class Payment(TimeStampedModel):
    booking = models.ForeignKey(
        "bookings.Booking", on_delete=models.PROTECT, related_name="payments"
    )
    amount = models.DecimalField(
        "montant", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.XOF)
    method = models.CharField("moyen de paiement", max_length=15, choices=PaymentMethod.choices)
    status = models.CharField(
        "statut", max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING,
        db_index=True,
    )

    class Meta:
        verbose_name = "paiement"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.booking.reference} — {self.amount} {self.currency} ({self.status})"


class PaymentTransaction(TimeStampedModel):
    """Échange avec un prestataire ; provider_reference unique rend les webhooks idempotents."""

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="transactions")
    provider = models.CharField("prestataire", max_length=30)
    provider_reference = models.CharField("référence prestataire", max_length=100, unique=True)
    status = models.CharField(
        "statut", max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    raw_response = models.JSONField("réponse brute", default=dict, blank=True)

    class Meta:
        verbose_name = "transaction"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider} {self.provider_reference}"
