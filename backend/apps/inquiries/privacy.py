"""Données personnelles des demandes de devis et des messages de contact (apps/core/privacy.py)."""
from django.utils import timezone

from apps.core import privacy

from .models import ContactMessage, QuoteRequest

# Champs effacés d'un devis ; le projet (destination, dates, voyageurs, budget) reste
# pour les statistiques de l'agence. Les textes libres peuvent contenir des noms.
QUOTE_ERASED = {
    "first_name": privacy.ANONYMOUS, "last_name": "", "email": "", "phone": "",
    "whatsapp": "", "country_code": "", "comments": "", "accommodation_pref": "",
    "transport_pref": "", "proposal_message": "",
}


def anonymize_quotes(queryset):
    return queryset.exclude(email="").update(**QUOTE_ERASED, updated_at=timezone.now())


@privacy.register
class ContactMessages(privacy.PersonalDataSource):
    label = "Messages de contact"

    def find(self, email):
        return ContactMessage.objects.filter(email__iexact=email)

    def export(self, obj):
        return {
            "date": obj.created_at.isoformat(), "nom": obj.name, "email": obj.email,
            "telephone": obj.phone, "objet": obj.subject, "message": obj.message,
            "statut": obj.get_status_display(),
        }

    def describe(self, obj):
        return f"{obj.created_at:%d/%m/%Y} — {obj.subject}"

    def apply_retention(self, now):
        cutoff = privacy.retention_cutoff("contact_messages", now)
        deleted, _ = ContactMessage.objects.filter(created_at__lt=cutoff).delete()
        return deleted


@privacy.register
class QuoteRequests(privacy.PersonalDataSource):
    label = "Demandes de devis"

    def find(self, email):
        # Y compris les devis supprimés (suppression logique) : ils contiennent les mêmes données.
        return (QuoteRequest.all_objects.filter(email__iexact=email)
                .select_related("booking").order_by("created_at"))

    def export(self, obj):
        return {
            "reference": obj.reference, "date": obj.created_at.isoformat(),
            "prenom": obj.first_name, "nom": obj.last_name, "email": obj.email,
            "telephone": obj.phone, "whatsapp": obj.whatsapp, "pays": obj.country_code,
            "destination": obj.destination_text or (obj.destination and str(obj.destination)) or "",
            "depart": obj.date_departure and obj.date_departure.isoformat(),
            "retour": obj.date_return and obj.date_return.isoformat(),
            "adultes": obj.adults, "enfants": obj.children,
            "budget": obj.budget and str(obj.budget), "devise": obj.currency,
            "commentaires": obj.comments, "statut": obj.get_status_display(),
            "consentement": obj.consent_at and obj.consent_at.isoformat(),
        }

    def describe(self, obj):
        return f"{obj.reference} — {obj.get_status_display()}"

    def decide(self, obj):
        booking = getattr(obj, "booking", None)
        if booking is not None:
            return privacy.KEEP, f"suit la réservation {booking.reference}"
        return privacy.ANONYMIZE, ""

    def anonymize(self, obj):
        anonymize_quotes(QuoteRequest.all_objects.filter(pk=obj.pk))

    def apply_retention(self, now):
        cutoff = privacy.retention_cutoff("quotes", now)
        return anonymize_quotes(QuoteRequest.all_objects.filter(
            updated_at__lt=cutoff, booking__isnull=True))
