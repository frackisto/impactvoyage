"""
Cycle de vie des réservations (architecture § 3.8).

Toute modification de statut passe par ce module. Le stock (places des
départs, véhicules, chambres, résidences, activités) est réservé et libéré
dans la même transaction que le changement de statut, sous verrou de ligne
(select_for_update) : deux confirmations simultanées ne peuvent pas prendre
la même place. La base garde le dernier mot (CheckConstraint, ExclusionConstraint).
"""
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from apps.accommodations.models import Residence, Room
from apps.activities.models import Activity
from apps.core.exceptions import BusinessError, InvalidToken, InvalidTransition, NotAvailable
from apps.core.formatting import format_amount
from apps.core.models import BookableMixin
from apps.notifications.emails import send_email
from apps.notifications.models import Notification
from apps.notifications.services import admin_path, notify_staff
from apps.offers.selectors import promo_price_for
from apps.tours.models import TourDeparture
from apps.vehicles.models import Vehicle

from . import selectors
from .models import BOOKING_TARGETS, Booking, BookingItem

Status = Booking.Status

ALLOWED_TRANSITIONS = {
    Status.REQUESTED: {Status.CONFIRMED, Status.REJECTED, Status.CANCELLED},
    Status.PENDING: {Status.CONFIRMED, Status.EXPIRED, Status.CANCELLED},
    Status.CONFIRMED: {Status.COMPLETED, Status.CANCELLED},
}

# Le client peut annuler lui-même tant que la réservation n'est pas confirmée ;
# ensuite, l'annulation passe par l'agence (CdC § 11 « changements et annulations »).
CUSTOMER_CANCELLABLE = frozenset({Status.REQUESTED, Status.PENDING})


@dataclass(frozen=True)
class ItemRequest:
    """
    Ce que le client demande : une offre, des dates, une quantité. Jamais de prix.
    - tour_departure : quantity = nombre de voyageurs (dates du départ) ;
    - room / residence : start_date = arrivée, end_date = départ ;
    - vehicle : start_date = prise en charge, end_date = restitution ;
    - activity : start_date = date, quantity = participants.
    """

    kind: str
    object_id: int
    start_date: date | None = None
    end_date: date | None = None
    quantity: int = 1
    pickup_location: str = ""
    dropoff_location: str = ""


@dataclass
class PricedItem:
    item: BookingItem
    booking_mode: str
    currency: str


# --- Tarification -----------------------------------------------------------


def _best_price(target, base_price):
    promo = promo_price_for(target)
    return min(base_price, promo) if promo is not None else base_price


def _require_period(req, today, unit_label):
    if not req.start_date or not req.end_date:
        raise BusinessError("Les dates de début et de fin sont obligatoires.", code="dates_required")
    if req.start_date < today:
        raise BusinessError("La date de début est déjà passée.", code="date_in_past")
    length = (req.end_date - req.start_date).days
    if length < 1:
        raise BusinessError(
            f"La réservation doit durer au moins un(e) {unit_label}.", code="invalid_period"
        )
    return length


def _not_found(req):
    return BusinessError("Cette offre n'est pas disponible.", code="offer_not_found",
                         details={"kind": req.kind, "id": req.object_id})


def price_item(req, today=None):
    """Construit une ligne de réservation (non enregistrée) avec son prix calculé côté serveur."""
    today = today or timezone.localdate()
    if req.kind not in BOOKING_TARGETS:
        raise BusinessError(f"Type d'offre inconnu : {req.kind}.", code="unknown_kind")
    if req.quantity < 1:
        raise BusinessError("La quantité doit être d'au moins 1.", code="invalid_quantity")

    fields = {"quantity": req.quantity}

    if req.kind == "tour_departure":
        departure = (
            TourDeparture.objects.select_related("tour")
            .filter(pk=req.object_id, tour__is_published=True).first()
        )
        if departure is None:
            raise _not_found(req)
        if departure.status != TourDeparture.Status.OPEN or departure.start_date < today:
            raise NotAvailable("Ce départ n'est plus ouvert à la réservation.")
        if req.quantity > departure.seats_left:
            raise NotAvailable(
                f"Il ne reste que {departure.seats_left} place(s) sur ce départ.",
                details={"seats_left": departure.seats_left},
            )
        target, owner = departure, departure.tour
        unit = _best_price(owner, departure.price)
        fields |= {
            "label": f"{owner.title} — départ du {departure.start_date:%d/%m/%Y}",
            "start_date": departure.start_date,
            "end_date": departure.end_date + timedelta(days=1),
            "line_total": unit * req.quantity,
        }

    elif req.kind == "room":
        target = (
            Room.objects.select_related("hotel")
            .filter(pk=req.object_id, is_active=True, hotel__is_published=True).first()
        )
        if target is None:
            raise _not_found(req)
        owner = target
        nights = _require_period(req, today, "nuit")
        if req.quantity > target.quantity:
            raise NotAvailable(f"Cet hôtel ne propose que {target.quantity} chambre(s) de ce type.")
        unit = target.base_price
        fields |= {
            "label": f"{target.hotel.name} — {target.name} ({nights} nuit(s))",
            "line_total": unit * nights * req.quantity,
        }

    elif req.kind == "residence":
        target = Residence.objects.filter(pk=req.object_id, is_published=True).first()
        if target is None:
            raise _not_found(req)
        owner = target
        nights = _require_period(req, today, "nuit")
        unit = _best_price(target, target.base_price)
        fields |= {
            "quantity": 1,
            "label": f"{target.name} ({nights} nuit(s))",
            "line_total": unit * nights,
        }

    elif req.kind == "vehicle":
        target = Vehicle.objects.filter(pk=req.object_id, is_published=True).first()
        if target is None:
            raise _not_found(req)
        owner = target
        days = _require_period(req, today, "jour")
        unit = _best_price(target, target.base_price)
        fields |= {
            "quantity": 1,
            "label": f"{target.brand} {target.model} ({days} jour(s))",
            "line_total": unit * days,
            "pickup_location": req.pickup_location,
            "dropoff_location": req.dropoff_location,
        }

    else:  # activity
        target = Activity.objects.filter(pk=req.object_id, is_published=True).first()
        if target is None:
            raise _not_found(req)
        owner = target
        if not req.start_date or req.start_date < today:
            raise BusinessError("Choisissez une date à venir.", code="date_in_past")
        if target.max_participants and req.quantity > target.max_participants:
            raise NotAvailable(f"Maximum {target.max_participants} participant(s).")
        unit = _best_price(target, target.base_price)
        fields |= {
            "label": f"{target.title} — {req.start_date:%d/%m/%Y}",
            "start_date": req.start_date,
            "end_date": req.start_date + timedelta(days=1),
            "line_total": unit * req.quantity,
        }

    fields.setdefault("start_date", req.start_date)
    fields.setdefault("end_date", req.end_date)
    item = BookingItem(unit_price=unit, **{req.kind: target}, **fields)
    return PricedItem(item=item, booking_mode=owner.booking_mode, currency=owner.currency)


# --- Stock ------------------------------------------------------------------


def _check_soft_availability(item):
    """Vérification sans verrou, pour refuser tôt une demande manifestement impossible."""
    if item.vehicle_id and not selectors.vehicle_is_available(
        item.vehicle, item.start_date, item.end_date
    ):
        raise NotAvailable("Ce véhicule est déjà réservé sur ces dates.")
    if item.residence_id and not selectors.residence_is_available(
        item.residence, item.start_date, item.end_date
    ):
        raise NotAvailable("Cette résidence est déjà réservée sur ces dates.")
    if item.room_id and selectors.room_units_left(
        item.room, item.start_date, item.end_date
    ) < item.quantity:
        raise NotAvailable("Plus assez de chambres de ce type sur ces dates.")
    if item.activity_id:
        left = selectors.activity_places_left(item.activity, item.start_date)
        if left is not None and left < item.quantity:
            raise NotAvailable(f"Il ne reste que {left} place(s) à cette date.")


def _block_stock(booking):
    """Réserve le stock de toutes les lignes. À appeler dans une transaction."""
    items = list(booking.items.all())

    seats_needed = defaultdict(int)
    for item in items:
        if item.tour_departure_id:
            seats_needed[item.tour_departure_id] += item.quantity
    departures = TourDeparture.objects.select_for_update().filter(pk__in=seats_needed).order_by("pk")
    for departure in departures:
        needed = seats_needed[departure.pk]
        if departure.status != TourDeparture.Status.OPEN or departure.seats_left < needed:
            raise NotAvailable(
                f"Plus assez de places sur le départ du {departure.start_date:%d/%m/%Y} "
                f"({departure.seats_left} restante(s)).",
                details={"departure": departure.pk, "seats_left": departure.seats_left},
            )
        departure.seats_reserved += needed
        if departure.seats_left == 0:
            departure.status = TourDeparture.Status.FULL
        departure.save(update_fields=["seats_reserved", "status", "updated_at"])

    # Verrou sur chaque ressource concernée, puis contrôle des chevauchements.
    for item in sorted(items, key=lambda i: (i.vehicle_id or 0, i.residence_id or 0,
                                             i.room_id or 0, i.activity_id or 0)):
        if item.vehicle_id:
            Vehicle.objects.select_for_update().get(pk=item.vehicle_id)
        elif item.residence_id:
            Residence.objects.select_for_update().get(pk=item.residence_id)
        elif item.room_id:
            Room.objects.select_for_update().get(pk=item.room_id)
        elif item.activity_id:
            Activity.objects.select_for_update().get(pk=item.activity_id)
        else:
            continue
        _check_soft_availability(item)

    try:
        with transaction.atomic():
            booking.items.update(is_blocking=True)
    except IntegrityError as exc:  # filet de sécurité : bookingitem_vehicle_no_overlap
        raise NotAvailable("Ce véhicule est déjà réservé sur ces dates.") from exc


def _release_stock(booking):
    """Libère le stock réservé par les lignes actives. À appeler dans une transaction."""
    items = list(booking.items.filter(is_blocking=True))
    seats = defaultdict(int)
    for item in items:
        if item.tour_departure_id:
            seats[item.tour_departure_id] += item.quantity
    for departure in TourDeparture.objects.select_for_update().filter(pk__in=seats).order_by("pk"):
        departure.seats_reserved = max(departure.seats_reserved - seats[departure.pk], 0)
        if departure.status == TourDeparture.Status.FULL and departure.seats_left > 0:
            departure.status = TourDeparture.Status.OPEN
        departure.save(update_fields=["seats_reserved", "status", "updated_at"])
    booking.items.update(is_blocking=False)


def _lock(booking, new_status):
    locked = Booking.objects.select_for_update().get(pk=booking.pk)
    if new_status not in ALLOWED_TRANSITIONS.get(locked.status, set()):
        raise InvalidTransition(
            f"Impossible de passer une réservation « {locked.get_status_display()} » "
            f"à « {Status(new_status).label} ».",
            details={"from": locked.status, "to": new_status},
        )
    return locked


def client_booking_url(booking):
    """Lien de suivi sans compte, envoyé dans chaque email au client."""
    return f"{settings.FRONTEND_URL}/reservation/{booking.reference}?token={booking.access_token}"


# --- Emails client (texte brut ; gabarits HTML en Phase 20) -------------------


def _email_customer(booking, subject, intro):
    lines = "\n".join(
        f"- {item.label} : {format_amount(item.line_total, booking.currency)}"
        for item in booking.items.all()
    )
    body = (
        f"Bonjour {booking.contact_name},\n\n{intro}\n\n"
        f"Référence : {booking.reference}\n{lines}\n"
        f"Total : {format_amount(booking.total_amount, booking.currency)}\n\n"
        f"Suivre votre réservation : {client_booking_url(booking)}\n\n"
        "L'équipe Impact Voyage"
    )
    send_email(booking.contact_email, f"{subject} — {booking.reference}", body)


# --- Cas d'usage ------------------------------------------------------------


def request_booking(
    *, contact_name, contact_email, contact_phone, items, user=None,
    customer_comments="", language="fr", consent=False,
):
    """
    Demande de réservation publique (CdC § 12, § 13, § 38). Les offres « sur
    demande » créent une demande (REQUESTED) qui ne bloque rien ; si toutes les
    offres sont en réservation directe, la réservation est PENDING et bloque le
    stock jusqu'à expires_at.
    """
    if not items:
        raise BusinessError("Aucune prestation sélectionnée.", code="empty_booking")
    priced = [price_item(req) for req in items]
    currencies = {p.currency for p in priced}
    if len(currencies) > 1:
        raise BusinessError("Les prestations doivent être dans la même devise.",
                            code="mixed_currencies")
    for p in priced:
        _check_soft_availability(p.item)

    instant = all(p.booking_mode == BookableMixin.BookingMode.INSTANT for p in priced)
    with transaction.atomic():
        booking = Booking.objects.create(
            user=user,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            customer_comments=customer_comments,
            language=language,
            consent_at=timezone.now() if consent else None,
            status=Status.PENDING if instant else Status.REQUESTED,
            expires_at=(
                timezone.now() + timedelta(minutes=settings.BOOKING_HOLD_MINUTES)
                if instant else None
            ),
            currency=currencies.pop(),
            total_amount=sum((p.item.line_total for p in priced), Decimal("0")),
        )
        for p in priced:
            p.item.booking = booking
        BookingItem.objects.bulk_create([p.item for p in priced])
        if instant:
            _block_stock(booking)

        notify_staff(
            Notification.Event.BOOKING_REQUESTED,
            f"Demande de réservation {booking.reference}",
            f"{contact_name} — {format_amount(booking.total_amount, booking.currency)}",
            link=admin_path(booking),
            related_object=booking,
        )
        _email_customer(
            booking,
            "Demande de réservation reçue",
            "Nous avons bien reçu votre demande. Un conseiller vous répondra rapidement.",
        )
    return booking


@transaction.atomic
def create_booking_from_quote(quote):
    """Réservation issue d'un devis accepté (appelée par inquiries.services.accept_quote)."""
    booking = Booking.objects.create(
        user=None,
        quote=quote,
        contact_name=f"{quote.first_name} {quote.last_name}",
        contact_email=quote.email,
        contact_phone=quote.phone,
        language=quote.language,
        consent_at=quote.consent_at,
        status=Status.PENDING,
        expires_at=timezone.now() + timedelta(hours=settings.QUOTE_BOOKING_HOLD_HOURS),
        total_amount=quote.proposal_amount or Decimal("0"),
        currency=quote.currency,
    )
    return booking


@transaction.atomic
def confirm_booking(booking, internal_notes=None):
    """Staff : accepte une demande (REQUESTED) ou confirme une réservation PENDING."""
    locked = _lock(booking, Status.CONFIRMED)
    if locked.status == Status.REQUESTED:
        _block_stock(locked)
    locked.status = Status.CONFIRMED
    locked.expires_at = None
    if internal_notes is not None:
        locked.internal_notes = internal_notes
    locked.save(update_fields=["status", "expires_at", "internal_notes", "updated_at"])
    _email_customer(locked, "Réservation confirmée", "Bonne nouvelle : votre réservation est confirmée.")
    return locked


@transaction.atomic
def reject_booking(booking, reason=""):
    """Staff : refuse une demande (aucun stock n'était réservé)."""
    locked = _lock(booking, Status.REJECTED)
    locked.status = Status.REJECTED
    locked.internal_notes = "\n".join(filter(None, [locked.internal_notes, reason]))
    locked.save(update_fields=["status", "internal_notes", "updated_at"])
    intro = "Nous sommes désolés : nous ne pouvons pas donner suite à votre demande."
    _email_customer(locked, "Demande de réservation", f"{intro}\n{reason}".strip())
    return locked


@transaction.atomic
def cancel_booking(booking, reason="", by_customer=False):
    """
    Annule et libère le stock éventuellement réservé. Le client (by_customer)
    ne peut annuler qu'avant confirmation ; le statut est contrôlé sous verrou.
    """
    locked = _lock(booking, Status.CANCELLED)
    if by_customer and locked.status not in CUSTOMER_CANCELLABLE:
        raise InvalidTransition(
            "Cette réservation est confirmée : contactez l'agence pour l'annuler.",
            code="contact_agency",
        )
    if locked.status in Booking.BLOCKING_STATUSES:
        _release_stock(locked)
    locked.status = Status.CANCELLED
    locked.expires_at = None
    locked.internal_notes = "\n".join(filter(None, [locked.internal_notes, reason]))
    locked.save(update_fields=["status", "expires_at", "internal_notes", "updated_at"])
    if by_customer:
        notify_staff(
            Notification.Event.BOOKING_CANCELLED,
            f"Réservation {locked.reference} annulée par le client",
            reason,
            link=admin_path(locked),
            related_object=locked,
        )
    _email_customer(locked, "Réservation annulée", "Votre réservation a bien été annulée.")
    return locked


def get_booking_for_client(reference, token):
    """Réservation consultée par le client via son lien secret (sans compte)."""
    try:
        token = uuid.UUID(str(token))
    except ValueError:
        raise InvalidToken("Lien de réservation invalide ou expiré.") from None
    booking = selectors.booking_detail_queryset().filter(
        reference=reference, access_token=token
    ).first()
    if booking is None:
        raise InvalidToken("Lien de réservation invalide ou expiré.")
    return booking


def expire_pending_bookings(now=None):
    """Tâche périodique : PENDING dont le délai est dépassé → EXPIRED, stock libéré."""
    now = now or timezone.now()
    expired = 0
    for pk in Booking.objects.filter(status=Status.PENDING, expires_at__lte=now).values_list(
        "pk", flat=True
    ):
        with transaction.atomic():
            locked = Booking.objects.select_for_update().get(pk=pk)
            if locked.status != Status.PENDING:  # confirmée entre-temps
                continue
            _release_stock(locked)
            locked.status = Status.EXPIRED
            locked.save(update_fields=["status", "updated_at"])
            expired += 1
    return expired


def complete_past_bookings(today=None):
    """Tâche quotidienne : réservations confirmées dont toutes les prestations sont passées."""
    today = today or timezone.localdate()
    done = list(
        Booking.objects.filter(status=Status.CONFIRMED)
        .annotate(last_day=Max("items__end_date"))
        .filter(last_day__lte=today)
        .values_list("pk", flat=True)
    )
    return Booking.objects.filter(pk__in=done, status=Status.CONFIRMED).update(
        status=Status.COMPLETED, updated_at=timezone.now()
    )
