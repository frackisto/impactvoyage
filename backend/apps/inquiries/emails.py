"""
Emails des devis et du formulaire de contact (Phase 20) : au client dans sa
langue, récapitulatifs des alertes envoyées à l'agence.
"""
from django.utils import translation
from django.utils.formats import date_format

from apps.core.choices import RequestedService
from apps.core.formatting import format_amount
from apps.notifications.emails import Email, frontend_url, normalize_language, pick


def client_quote_url(quote):
    """Lien de suivi et de validation du devis, dans la langue du client."""
    return frontend_url(f"/devis/{quote.reference}?token={quote.access_token}", quote.language)


def _destination(quote):
    if quote.destination_text:
        return quote.destination_text
    return quote.destination.name if quote.destination else ""


def quote_details(quote, language):
    lang = normalize_language(language)
    with translation.override(lang):
        details = [(pick(lang, "Référence", "Reference"), quote.reference)]
        if destination := _destination(quote):
            details.append(("Destination", destination))
        if quote.date_departure:
            dates = date_format(quote.date_departure, "DATE_FORMAT")
            if quote.date_return:
                dates = pick(lang, f"Du {dates} au ", f"From {dates} to ") + date_format(
                    quote.date_return, "DATE_FORMAT")
            details.append(("Dates", dates))
        details.append((pick(lang, "Voyageurs", "Travellers"), pick(
            lang, f"{quote.adults} adulte(s), {quote.children} enfant(s)",
            f"{quote.adults} adult(s), {quote.children} child(ren)")))
    return details


def _greeting(lang, first_name):
    return pick(lang, f"Bonjour {first_name},", f"Hello {first_name},")


def quote_received(quote):
    lang = normalize_language(quote.language)
    return Email(
        subject=pick(lang, f"Votre demande de devis {quote.reference}",
                     f"Your quote request {quote.reference}"),
        heading=pick(lang, "Nous avons bien reçu votre demande de devis",
                     "We have received your quote request"),
        language=lang,
        greeting=_greeting(lang, quote.first_name),
        paragraphs=[pick(
            lang,
            "Merci pour votre confiance ! Un conseiller étudie votre projet et vous envoie une "
            "proposition personnalisée rapidement, en général sous 48 heures ouvrées.",
            "Thank you for your trust! An advisor is studying your project and will send you "
            "a personalised proposal shortly, usually within two business days.",
        )],
        details=quote_details(quote, lang),
        action=(pick(lang, "Suivre ma demande", "Track my request"), client_quote_url(quote)),
    )


def proposal_sent(quote):
    lang = normalize_language(quote.language)
    with translation.override(lang):
        valid_until = date_format(quote.proposal_valid_until, "DATE_FORMAT")
    details = quote_details(quote, lang) + [
        (pick(lang, "Montant proposé", "Proposed price"),
         format_amount(quote.proposal_amount, quote.currency, lang)),
        (pick(lang, "Valable jusqu'au", "Valid until"), valid_until),
    ]
    return Email(
        subject=pick(lang, f"Votre proposition de voyage {quote.reference}",
                     f"Your travel proposal {quote.reference}"),
        heading=pick(lang, "Votre proposition de voyage est prête",
                     "Your travel proposal is ready"),
        language=lang,
        greeting=_greeting(lang, quote.first_name),
        paragraphs=[quote.proposal_message],
        details=details,
        action=(pick(lang, "Voir et valider la proposition", "View and accept the proposal"),
                client_quote_url(quote)),
        note=pick(lang, "Vous pouvez aussi la refuser depuis la même page. Passé la date de "
                        "validité, contactez-nous pour la renouveler.",
                  "You can also decline it from the same page. After the validity date, "
                  "contact us to renew it."),
    )


def quote_accepted(quote, booking):
    from apps.bookings.emails import client_booking_url

    lang = normalize_language(quote.language)
    return Email(
        subject=pick(lang, f"Proposition acceptée — {booking.reference}",
                     f"Proposal accepted — {booking.reference}"),
        heading=pick(lang, "Merci, votre réservation est enregistrée",
                     "Thank you, your booking is registered"),
        language=lang,
        greeting=_greeting(lang, quote.first_name),
        paragraphs=[pick(
            lang,
            "Vous avez accepté notre proposition : votre réservation est enregistrée. Un "
            "conseiller vous contacte pour finaliser le règlement.",
            "You have accepted our proposal: your booking is registered. An advisor will "
            "contact you to complete the payment.",
        )],
        details=[
            (pick(lang, "Réservation", "Booking"), booking.reference),
            (pick(lang, "Devis", "Quote"), quote.reference),
            ("Total", format_amount(booking.total_amount, booking.currency, lang)),
        ],
        action=(pick(lang, "Suivre ma réservation", "Track my booking"),
                client_booking_url(booking)),
    )


def contact_acknowledgement(contact):
    lang = normalize_language(contact.language)
    return Email(
        subject=pick(lang, "Nous avons bien reçu votre message", "We have received your message"),
        heading=pick(lang, "Merci pour votre message", "Thank you for your message"),
        language=lang,
        greeting=_greeting(lang, contact.name.split(" ")[0]),
        paragraphs=[pick(
            lang,
            "Nous avons bien reçu votre message et vous répondons rapidement, en général sous "
            "24 heures ouvrées. Pour une demande urgente, appelez-nous ou écrivez-nous sur "
            "WhatsApp.",
            "We have received your message and will reply shortly, usually within one "
            "business day. For an urgent request, call us or message us on WhatsApp.",
        )],
        details=[(pick(lang, "Objet", "Subject"), contact.subject),
                 ("Message", contact.message)],
    )


# --- Récapitulatifs des alertes de l'agence (en français) ----------------------


def quote_staff_details(quote):
    labels = dict(RequestedService.choices)
    details = [("Client", f"{quote.first_name} {quote.last_name}\n{quote.email}\n{quote.phone}"),
               *quote_details(quote, "fr")]
    if quote.budget is not None:
        details.append(("Budget", format_amount(quote.budget, quote.currency)))
    if quote.services_requested:
        details.append(("Services", ", ".join(labels.get(s, s) for s in quote.services_requested)))
    if quote.comments:
        details.append(("Commentaires", quote.comments))
    return details


def contact_staff_details(contact):
    return [("De", f"{contact.name}\n{contact.email}" + (f"\n{contact.phone}" if contact.phone else "")),
            ("Objet", contact.subject),
            ("Message", contact.message)]
