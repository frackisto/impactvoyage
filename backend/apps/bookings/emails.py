"""
Emails des réservations (Phase 20) : au client dans sa langue (booking.language),
et récapitulatif de l'alerte envoyée à l'agence.
"""
from django.conf import settings
from django.utils import timezone, translation
from django.utils.formats import date_format

from apps.core.formatting import format_amount
from apps.notifications.emails import Email, frontend_url, normalize_language, pick

LANGUAGE_NAMES = dict(settings.LANGUAGES)


def client_booking_url(booking):
    """Lien de suivi sans compte, dans la langue du client."""
    return frontend_url(
        f"/reservation/{booking.reference}?token={booking.access_token}", booking.language
    )


def _date(value):
    return date_format(value, "DATE_FORMAT")


def item_summary(item, language):
    """(prestation, dates et montant) d'une ligne, dans la langue du client."""
    lang = normalize_language(language)
    with translation.override(lang):  # champs traduits (modeltranslation) et dates
        amount = format_amount(item.line_total, item.booking.currency, lang)
        if item.tour_departure_id:
            departure = item.tour_departure
            name = departure.tour.title
            when = pick(lang, f"Départ le {_date(departure.start_date)}",
                        f"Departure on {_date(departure.start_date)}")
            count = pick(lang, f"{item.quantity} voyageur(s)", f"{item.quantity} traveller(s)")
        elif item.activity_id:
            name = item.activity.title
            when = _date(item.start_date)
            count = pick(lang, f"{item.quantity} participant(s)", f"{item.quantity} participant(s)")
        else:
            nights = (item.end_date - item.start_date).days
            if item.room_id:
                name = f"{item.room.hotel.name} — {item.room.name}"
            elif item.residence_id:
                name = item.residence.name
            else:
                name = f"{item.vehicle.brand} {item.vehicle.model}"
            when = pick(lang, f"Du {_date(item.start_date)} au {_date(item.end_date)}",
                        f"From {_date(item.start_date)} to {_date(item.end_date)}")
            if item.vehicle_id:
                count = pick(lang, f"{nights} jour(s)", f"{nights} day(s)")
            elif item.room_id:
                count = pick(lang, f"{nights} nuit(s), {item.quantity} chambre(s)",
                             f"{nights} night(s), {item.quantity} room(s)")
            else:
                count = pick(lang, f"{nights} nuit(s)", f"{nights} night(s)")
    return name, f"{when}\n{count} — {amount}"


def booking_details(booking, language):
    lang = normalize_language(language)
    details = [(pick(lang, "Référence", "Reference"), booking.reference)]
    details += [item_summary(item, lang) for item in booking.items.all()]
    details.append(("Total", format_amount(booking.total_amount, booking.currency, lang)))
    return details


def _client_email(booking, *, subject, heading, paragraphs, note=""):
    lang = normalize_language(booking.language)
    first_name = booking.contact_name.split(" ")[0]
    return Email(
        subject=f"{subject} — {booking.reference}",
        heading=heading,
        language=lang,
        greeting=pick(lang, f"Bonjour {first_name},", f"Hello {first_name},"),
        paragraphs=paragraphs,
        details=booking_details(booking, lang),
        action=(pick(lang, "Suivre ma réservation", "Track my booking"), client_booking_url(booking)),
        note=note,
    )


def booking_received(booking):
    lang = booking.language
    if booking.expires_at:
        with translation.override(normalize_language(lang)):
            until = date_format(timezone.localtime(booking.expires_at), "DATETIME_FORMAT")
        paragraphs = [pick(
            lang,
            f"Votre réservation est enregistrée et les places sont bloquées jusqu'au {until}. "
            "Un conseiller vous contacte pour finaliser le règlement.",
            f"Your booking is registered and the places are held until {until}. "
            "An advisor will contact you to complete the payment.",
        )]
    else:
        paragraphs = [pick(
            lang,
            "Nous avons bien reçu votre demande de réservation. Un conseiller vérifie la "
            "disponibilité et vous répond rapidement, en général sous 24 heures ouvrées.",
            "We have received your booking request. An advisor is checking availability "
            "and will reply shortly, usually within one business day.",
        )]
    return _client_email(
        booking,
        subject=pick(lang, "Demande de réservation reçue", "Booking request received"),
        heading=pick(lang, "Nous avons bien reçu votre demande", "We have received your request"),
        paragraphs=paragraphs,
        note=pick(lang, "Vous pouvez annuler votre demande depuis la page de suivi tant "
                        "qu'elle n'est pas confirmée.",
                  "You can cancel your request from the tracking page until it is confirmed."),
    )


def booking_confirmed(booking):
    lang = booking.language
    return _client_email(
        booking,
        subject=pick(lang, "Réservation confirmée", "Booking confirmed"),
        heading=pick(lang, "Votre réservation est confirmée", "Your booking is confirmed"),
        paragraphs=[pick(
            lang,
            "Bonne nouvelle : votre réservation est confirmée. Conservez cet email, la "
            "référence vous sera demandée. Un conseiller reste à votre disposition pour "
            "toute question.",
            "Good news: your booking is confirmed. Please keep this email, you will be asked "
            "for the reference. An advisor remains available for any question.",
        )],
        note=pick(lang, "Pour modifier ou annuler une réservation confirmée, contactez-nous.",
                  "To change or cancel a confirmed booking, please contact us."),
    )


def booking_rejected(booking, reason=""):
    lang = booking.language
    paragraphs = [pick(
        lang,
        "Nous sommes désolés : nous ne pouvons pas donner suite à votre demande de réservation.",
        "We are sorry: we are unable to accept your booking request.",
    )]
    if reason:
        paragraphs.append(pick(lang, f"Motif : {reason}", f"Reason: {reason}"))
    paragraphs.append(pick(
        lang,
        "Nous pouvons vous proposer une alternative : répondez à cet email ou demandez un "
        "devis sur notre site.",
        "We can offer you an alternative: reply to this email or request a quote on our website.",
    ))
    email = _client_email(
        booking,
        subject=pick(lang, "Demande de réservation non retenue", "Booking request declined"),
        heading=pick(lang, "Votre demande n'a pas pu être acceptée",
                     "Your request could not be accepted"),
        paragraphs=paragraphs,
    )
    email.action = (pick(lang, "Demander un devis", "Request a quote"), frontend_url("/devis", lang))
    return email


def booking_cancelled(booking, by_customer):
    lang = booking.language
    if by_customer:
        paragraph = pick(lang, "Votre annulation est bien enregistrée. Aucun frais ne vous "
                               "sera demandé pour cette demande.",
                         "Your cancellation has been recorded. No fee will be charged for "
                         "this request.")
    else:
        paragraph = pick(lang, "Votre réservation a été annulée par notre équipe. Un conseiller "
                               "vous contacte pour vous en expliquer la raison et vous proposer "
                               "une solution.",
                         "Your booking has been cancelled by our team. An advisor will contact "
                         "you to explain why and offer a solution.")
    return _client_email(
        booking,
        subject=pick(lang, "Réservation annulée", "Booking cancelled"),
        heading=pick(lang, "Votre réservation est annulée", "Your booking is cancelled"),
        paragraphs=[paragraph],
    )


def booking_expired(booking):
    lang = booking.language
    email = _client_email(
        booking,
        subject=pick(lang, "Réservation expirée", "Booking expired"),
        heading=pick(lang, "Votre réservation a expiré", "Your booking has expired"),
        paragraphs=[pick(
            lang,
            "Le délai de validation de votre réservation est dépassé : elle a expiré et les "
            "places ont été libérées. Contactez-nous ou faites une nouvelle demande pour "
            "réserver à nouveau.",
            "The time limit to validate your booking has passed: it has expired and the "
            "places have been released. Contact us or make a new request to book again.",
        )],
    )
    email.action = (pick(lang, "Nous contacter", "Contact us"), frontend_url("/contact", lang))
    return email


def staff_details(booking):
    """Récapitulatif des alertes de l'agence (en français)."""
    details = [
        ("Client", f"{booking.contact_name}\n{booking.contact_email}\n{booking.contact_phone}"),
        *booking_details(booking, "fr"),
        ("Langue du client", LANGUAGE_NAMES.get(booking.language, booking.language)),
    ]
    if booking.customer_comments:
        details.append(("Commentaires", booking.customer_comments))
    return details
