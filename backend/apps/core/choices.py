"""Choix partagés entre plusieurs apps."""
from django.db import models


class Currency(models.TextChoices):
    XOF = "XOF", "Franc CFA (FCFA)"
    EUR = "EUR", "Euro"
    USD = "USD", "Dollar américain"
    GBP = "GBP", "Livre sterling"


class RequestedService(models.TextChoices):
    """Prestations demandables dans un devis (CdC § 11, § 18)."""

    VOL = "VOL", "Billet d'avion"
    HEBERGEMENT = "HEBERGEMENT", "Hébergement"
    CIRCUIT = "CIRCUIT", "Circuit / excursion"
    VISA = "VISA", "Visa et formalités"
    ASSURANCE = "ASSURANCE", "Assurance voyage"
    TRANSPORT = "TRANSPORT", "Transport"
    LOCATION_VEHICULE = "LOCATION_VEHICULE", "Location de véhicule"
    ACTIVITES = "ACTIVITES", "Activités"
    EVENEMENT = "EVENEMENT", "Organisation d'événement"
    CONSEIL = "CONSEIL", "Conseil et planification"
