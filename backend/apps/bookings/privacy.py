"""Données personnelles des réservations (apps/core/privacy.py)."""
from django.db.models import Q
from django.utils import timezone

from apps.core import privacy
from apps.inquiries.models import QuoteRequest
from apps.inquiries.privacy import anonymize_quotes

from .models import Booking, BookingItem

Status = Booking.Status
CLOSED = (Status.CANCELLED, Status.REJECTED, Status.EXPIRED)
IN_PROGRESS = (Status.REQUESTED, Status.PENDING)
# Pièces comptables : conservées pendant la durée légale (10 ans, droit OHADA).
ACCOUNTING = (Status.CONFIRMED, Status.COMPLETED)

BOOKING_ERASED = {
    "contact_name": privacy.ANONYMOUS, "contact_email": "", "contact_phone": "",
    "customer_comments": "", "internal_notes": "", "user": None,
}


def anonymize_bookings(queryset):
    """Anonymise les réservations et leur devis d'origine ; renvoie le nombre de réservations."""
    ids = list(queryset.exclude(contact_email="").values_list("pk", flat=True))
    if not ids:
        return 0
    BookingItem.objects.filter(booking_id__in=ids).update(pickup_location="", dropoff_location="")
    anonymize_quotes(QuoteRequest.all_objects.filter(booking__in=ids))
    return Booking.all_objects.filter(pk__in=ids).update(**BOOKING_ERASED,
                                                         updated_at=timezone.now())


@privacy.register
class Bookings(privacy.PersonalDataSource):
    label = "Réservations"

    def find(self, email):
        return (Booking.all_objects
                .filter(Q(contact_email__iexact=email) | Q(user__email__iexact=email))
                .prefetch_related("items").order_by("created_at"))

    def export(self, obj):
        return {
            "reference": obj.reference, "date": obj.created_at.isoformat(),
            "nom": obj.contact_name, "email": obj.contact_email, "telephone": obj.contact_phone,
            "statut": obj.get_status_display(), "commentaires": obj.customer_comments,
            "montant": str(obj.total_amount), "devise": obj.currency,
            "prestations": [
                {"libelle": item.label, "debut": item.start_date.isoformat(),
                 "fin": item.end_date.isoformat(), "quantite": item.quantity,
                 "prise_en_charge": item.pickup_location, "restitution": item.dropoff_location}
                for item in obj.items.all()
            ],
            "consentement": obj.consent_at and obj.consent_at.isoformat(),
        }

    def describe(self, obj):
        return f"{obj.reference} — {obj.get_status_display()}"

    def decide(self, obj):
        if obj.status in ACCOUNTING:
            return privacy.KEEP, "obligation comptable (10 ans)"
        if obj.status in IN_PROGRESS:
            return privacy.KEEP, "demande en cours : refusez-la ou annulez-la d'abord"
        return privacy.ANONYMIZE, ""

    def anonymize(self, obj):
        anonymize_bookings(Booking.all_objects.filter(pk=obj.pk))

    def apply_retention(self, now):
        closed = Q(status__in=CLOSED, updated_at__lt=privacy.retention_cutoff("closed_bookings", now))
        completed = Q(status=Status.COMPLETED,
                      updated_at__lt=privacy.retention_cutoff("completed_bookings", now))
        return anonymize_bookings(Booking.all_objects.filter(closed | completed))
