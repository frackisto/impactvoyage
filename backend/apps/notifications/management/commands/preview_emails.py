"""
Aperçu des emails (Phase 20) : écrit chaque email, en français et en anglais,
dans un dossier (un fichier .html et un .txt par email), à partir des données
de démonstration. Rien n'est envoyé.

    python manage.py seed_demo
    python manage.py preview_emails --out /tmp/emails
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts import emails as account_emails
from apps.accounts.models import User
from apps.bookings import emails as booking_emails
from apps.bookings.models import Booking
from apps.inquiries import emails as inquiry_emails
from apps.inquiries.models import ContactMessage, QuoteRequest
from apps.notifications.channels import StaffAlert
from apps.notifications.emails import Email, render
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = "Écrit un aperçu HTML et texte de chaque email (FR et EN), sans rien envoyer."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="email-previews", help="Dossier de sortie.")

    def samples(self, lang):
        booking = Booking.objects.filter(reference="IV-DEMO-000001").first()
        quote = QuoteRequest.objects.filter(reference="DV-DEMO-000001").first()
        if booking is None or quote is None:
            raise CommandError("Données de démonstration absentes : lancez d'abord seed_demo.")
        booking.language = quote.language = lang
        # Objets non enregistrés : l'aperçu ne modifie rien.
        contact = ContactMessage(name="Awa Koné", email="awa@example.com", subject="Visa Canada",
                                 message="Bonjour, quels documents faut-il pour un visa ?",
                                 language=lang)
        user = User(email="awa@example.com", first_name="Awa", preferred_language=lang)
        if not quote.proposal_valid_until:
            quote.proposal_valid_until = timezone.localdate()
        yield "booking-received", booking_emails.booking_received(booking)
        yield "booking-confirmed", booking_emails.booking_confirmed(booking)
        yield "booking-rejected", booking_emails.booking_rejected(booking, "Villa en travaux.")
        yield "booking-cancelled-by-customer", booking_emails.booking_cancelled(booking, True)
        yield "booking-cancelled-by-agency", booking_emails.booking_cancelled(booking, False)
        yield "booking-expired", booking_emails.booking_expired(booking)
        yield "quote-received", inquiry_emails.quote_received(quote)
        yield "quote-proposal", inquiry_emails.proposal_sent(quote)
        yield "quote-accepted", inquiry_emails.quote_accepted(quote, booking)
        yield "contact-acknowledgement", inquiry_emails.contact_acknowledgement(contact)
        yield "account-verification", account_emails.verification(user, "exemple-de-jeton")
        yield "account-password-reset", account_emails.password_reset(user, "MQ", "jeton", 120)

    def agency_samples(self):
        booking = Booking.objects.get(reference="IV-DEMO-000001")
        alert = StaffAlert(
            event=Notification.Event.BOOKING_REQUESTED,
            title=f"Demande de réservation {booking.reference}",
            message=f"{booking.contact_name} — nouvelle demande à traiter.",
            link=f"/admin/bookings/booking/{booking.pk}/change/",
            details=booking_emails.staff_details(booking),
        )
        yield "agency-booking-requested", Email(
            subject=f"[Impact Voyage] {alert.title}", heading=alert.title,
            paragraphs=[alert.message], details=alert.details,
            action=("Ouvrir dans l'administration", alert.admin_url), for_agency=True,
        )

    def handle(self, *args, out, **options):
        folder = Path(out)
        folder.mkdir(parents=True, exist_ok=True)
        written = 0
        emails = [(f"{name}.{lang}", email) for lang in ("fr", "en")
                  for name, email in self.samples(lang)]
        emails += list(self.agency_samples())
        for name, email in emails:
            subject, text, html = render(email)
            (folder / f"{name}.html").write_text(html, encoding="utf-8")
            (folder / f"{name}.txt").write_text(f"Sujet : {subject}\n\n{text}", encoding="utf-8")
            written += 1
        self.stdout.write(self.style.SUCCESS(f"{written} emails écrits dans {folder.resolve()}."))
