"""
Devis et messages de contact (CdC § 18, § 19, § 38 ; architecture § 3.8).

Parcours d'un devis :
NOUVELLE → EN_COURS (commercial assigné) → DEVIS_ENVOYE (proposition + lien
client) → ACCEPTEE (le client valide via son lien : réservation PENDING créée)
ou REFUSEE → TERMINEE.
"""
import uuid

from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import BusinessError, InvalidToken, InvalidTransition
from apps.core.formatting import format_amount
from apps.notifications.emails import send_email
from apps.notifications.models import Notification
from apps.notifications.services import admin_path, notify_staff

from . import emails
from .emails import client_quote_url  # noqa: F401 (lien réexporté pour l'admin et les tests)
from .models import ContactMessage, QuoteRequest

QStatus = QuoteRequest.Status

QUOTE_TRANSITIONS = {
    QStatus.NOUVELLE: {QStatus.EN_COURS, QStatus.DEVIS_ENVOYE, QStatus.REFUSEE},
    QStatus.EN_COURS: {QStatus.DEVIS_ENVOYE, QStatus.REFUSEE},
    QStatus.DEVIS_ENVOYE: {QStatus.DEVIS_ENVOYE, QStatus.ACCEPTEE, QStatus.REFUSEE},
    QStatus.ACCEPTEE: {QStatus.TERMINEE},
}

CONTACT_TRANSITIONS = {
    ContactMessage.Status.NOUVEAU: {ContactMessage.Status.LU, ContactMessage.Status.TRAITE,
                                    ContactMessage.Status.ARCHIVE},
    ContactMessage.Status.LU: {ContactMessage.Status.TRAITE, ContactMessage.Status.ARCHIVE},
    ContactMessage.Status.TRAITE: {ContactMessage.Status.ARCHIVE},
}


def _lock_quote(quote, new_status):
    locked = QuoteRequest.objects.select_for_update().get(pk=quote.pk)
    if new_status not in QUOTE_TRANSITIONS.get(locked.status, set()):
        raise InvalidTransition(
            f"Impossible de passer un devis « {locked.get_status_display()} » "
            f"à « {QStatus(new_status).label} ».",
            details={"from": locked.status, "to": new_status},
        )
    return locked


def _notify_staff_about_quote(quote, event, title, message="", related_object=None):
    related = related_object or quote
    notify_staff(event, title, message, link=admin_path(related), related_object=related,
                 details=emails.quote_staff_details(quote), reply_to=[quote.email])


# --- Devis ------------------------------------------------------------------


@transaction.atomic
def create_quote_request(*, activities=(), **data):
    """
    Enregistre une demande de devis (CdC § 18) : enregistrement, email à
    l'agence, email de confirmation au client, notification dans l'administration.
    Le consentement au traitement des données est obligatoire.
    """
    if not data.pop("consent", False):
        raise BusinessError(
            "Vous devez accepter le traitement de vos données pour envoyer la demande.",
            code="consent_required",
        )
    quote = QuoteRequest(**data, consent_at=timezone.now(), status=QStatus.NOUVELLE)
    quote.full_clean(exclude=["reference", "activities"])
    quote.save()
    if activities:
        quote.activities.set(activities)

    _notify_staff_about_quote(
        quote,
        Notification.Event.QUOTE_CREATED,
        f"Nouvelle demande de devis {quote.reference}",
        f"{quote.first_name} {quote.last_name} — {quote.destination_text or quote.destination or 'destination libre'}",
    )
    send_email(quote.email, emails.quote_received(quote))
    return quote


@transaction.atomic
def assign_quote(quote, commercial):
    """Assigne un commercial ; un devis nouveau passe « En cours »."""
    if not commercial.is_staff:
        raise BusinessError("Seul un membre de l'équipe peut traiter un devis.",
                            code="not_staff")
    locked = QuoteRequest.objects.select_for_update().get(pk=quote.pk)
    locked.assigned_to = commercial
    fields = ["assigned_to", "updated_at"]
    if locked.status == QStatus.NOUVELLE:
        locked.status = QStatus.EN_COURS
        fields.append("status")
    locked.save(update_fields=fields)
    return locked


@transaction.atomic
def send_proposal(quote, *, amount, message, valid_until, by=None):
    """Envoie (ou renvoie) la proposition chiffrée au client, avec son lien de validation."""
    if amount is None or amount < 0:
        raise BusinessError("Le montant proposé est obligatoire.", code="amount_required")
    if valid_until < timezone.localdate():
        raise BusinessError("La date de validité est déjà passée.", code="date_in_past")
    locked = _lock_quote(quote, QStatus.DEVIS_ENVOYE)
    locked.proposal_amount = amount
    locked.proposal_message = message
    locked.proposal_valid_until = valid_until
    locked.proposal_sent_at = timezone.now()
    locked.status = QStatus.DEVIS_ENVOYE
    if by is not None and locked.assigned_to_id is None:
        locked.assigned_to = by
    locked.save()
    send_email(locked.email, emails.proposal_sent(locked))
    return locked


def get_quote_for_client(reference, token):
    """Devis consulté par le client via son lien secret (sans compte)."""
    try:
        token = uuid.UUID(str(token))
    except ValueError:
        raise InvalidToken("Lien de devis invalide ou expiré.") from None
    quote = QuoteRequest.objects.filter(reference=reference, access_token=token).first()
    if quote is None:
        raise InvalidToken("Lien de devis invalide ou expiré.")
    return quote


def _check_client_can_answer(quote):
    if quote.status != QStatus.DEVIS_ENVOYE:
        raise InvalidTransition("Ce devis n'attend pas de réponse.")
    if quote.proposal_valid_until and quote.proposal_valid_until < timezone.localdate():
        raise BusinessError(
            "Cette proposition a expiré. Contactez-nous pour la renouveler.",
            code="proposal_expired",
        )


@transaction.atomic
def accept_quote(reference, token):
    """Le client valide la proposition : devis ACCEPTEE et réservation PENDING créée."""
    from apps.bookings.services import create_booking_from_quote

    quote = get_quote_for_client(reference, token)
    locked = _lock_quote(quote, QStatus.ACCEPTEE)
    _check_client_can_answer(locked)
    locked.status = QStatus.ACCEPTEE
    locked.save(update_fields=["status", "updated_at"])
    booking = create_booking_from_quote(locked)

    _notify_staff_about_quote(
        locked,
        Notification.Event.QUOTE_ACCEPTED,
        f"Devis {locked.reference} accepté par le client",
        f"Réservation {booking.reference} créée — "
        f"{format_amount(booking.total_amount, booking.currency)}",
        related_object=booking,
    )
    send_email(locked.email, emails.quote_accepted(locked, booking))
    return booking


@transaction.atomic
def decline_quote(reference, token, reason=""):
    """Le client décline la proposition."""
    quote = get_quote_for_client(reference, token)
    locked = _lock_quote(quote, QStatus.REFUSEE)
    _check_client_can_answer(locked)
    locked.status = QStatus.REFUSEE
    if reason:
        locked.comments = "\n".join(filter(None, [locked.comments, f"Motif du refus : {reason}"]))
    locked.save(update_fields=["status", "comments", "updated_at"])
    _notify_staff_about_quote(
        locked,
        Notification.Event.QUOTE_DECLINED,
        f"Devis {locked.reference} refusé par le client",
        f"Motif : {reason}" if reason else "Aucun motif indiqué.",
    )
    return locked


@transaction.atomic
def change_quote_status(quote, new_status):
    """Staff : changement de statut manuel, dans le respect du parcours."""
    locked = _lock_quote(quote, new_status)
    locked.status = new_status
    locked.save(update_fields=["status", "updated_at"])
    return locked


# --- Contact ----------------------------------------------------------------


@transaction.atomic
def create_contact_message(*, name, email, subject, message, phone="", language="fr"):
    """Message de contact : alerte à l'agence (répondre = écrire au client), accusé de réception."""
    contact = ContactMessage(name=name, email=email, phone=phone, subject=subject,
                             message=message, language=language)
    contact.full_clean()
    contact.save()
    notify_staff(
        Notification.Event.CONTACT_RECEIVED,
        f"Message de {name} : {subject}",
        message[:500],
        link=admin_path(contact),
        related_object=contact,
        details=emails.contact_staff_details(contact),
        reply_to=[email],
    )
    send_email(email, emails.contact_acknowledgement(contact))
    return contact


def change_contact_status(contact, new_status):
    if new_status not in CONTACT_TRANSITIONS.get(contact.status, set()):
        raise InvalidTransition("Changement de statut impossible pour ce message.")
    contact.status = new_status
    contact.save(update_fields=["status", "updated_at"])
    return contact
