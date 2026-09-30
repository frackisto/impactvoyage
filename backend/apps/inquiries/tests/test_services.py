import uuid
from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from apps.bookings.models import Booking
from apps.core.exceptions import BusinessError, InvalidToken, InvalidTransition
from apps.core.tests.factories import UserFactory
from apps.inquiries import services
from apps.inquiries.models import ContactMessage, QuoteRequest
from apps.notifications.models import Notification

QUOTE = {
    "first_name": "Awa",
    "last_name": "Koné",
    "email": "awa@example.com",
    "phone": "+2250700000000",
    "destination_text": "Zanzibar",
    "adults": 2,
    "services_requested": ["VOL", "HEBERGEMENT"],
}


class QuoteFlowTests(TestCase):
    def setUp(self):
        self.commercial = UserFactory(role="COMMERCIAL")
        UserFactory(role="GESTIONNAIRE")

    def _create(self, **extra):
        return services.create_quote_request(**{**QUOTE, "consent": True, **extra})

    def test_consent_is_required(self):
        with self.assertRaises(BusinessError):
            services.create_quote_request(**QUOTE)

    def test_creation_saves_notifies_and_confirms(self):
        with self.captureOnCommitCallbacks(execute=True):
            quote = self._create()
        self.assertEqual(quote.status, QuoteRequest.Status.NOUVELLE)
        self.assertRegex(quote.reference, r"^DV-")
        self.assertIsNotNone(quote.consent_at)
        # Le commercial est prévenu, pas le gestionnaire.
        self.assertEqual(
            list(Notification.objects.values_list("recipient", flat=True)), [self.commercial.pk]
        )
        self.assertEqual(len(mail.outbox), 2)
        # Le client reçoit le lien de suivi de sa demande.
        confirmation = next(m for m in mail.outbox if m.to == [quote.email])
        self.assertIn(f"/devis/{quote.reference}?token={quote.access_token}", confirmation.body)

    def test_full_flow_until_client_acceptance(self):
        quote = services.assign_quote(self._create(), self.commercial)
        self.assertEqual(quote.status, QuoteRequest.Status.EN_COURS)

        with self.captureOnCommitCallbacks(execute=True):
            quote = services.send_proposal(
                quote, amount=Decimal("1850000"), message="Séjour 7 nuits tout compris.",
                valid_until=timezone.localdate() + timedelta(days=10),
            )
        self.assertEqual(quote.status, QuoteRequest.Status.DEVIS_ENVOYE)
        self.assertIn(str(quote.access_token), mail.outbox[-1].body)

        with self.assertRaises(InvalidToken):
            services.accept_quote(quote.reference, uuid.uuid4())

        with self.captureOnCommitCallbacks(execute=True):
            booking = services.accept_quote(quote.reference, quote.access_token)
        # L'email d'acceptation donne le lien de suivi de la réservation créée.
        link = f"/reservation/{booking.reference}?token={booking.access_token}"
        self.assertTrue(any(link in m.body for m in mail.outbox))
        quote.refresh_from_db()
        self.assertEqual(quote.status, QuoteRequest.Status.ACCEPTEE)
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.assertEqual(booking.total_amount, Decimal("1850000"))
        self.assertEqual(booking.quote, quote)

        with self.assertRaises(InvalidTransition):
            services.accept_quote(quote.reference, quote.access_token)

    def test_expired_proposal_cannot_be_accepted(self):
        quote = services.send_proposal(
            self._create(), amount=Decimal("100"), message="…",
            valid_until=timezone.localdate(),
        )
        QuoteRequest.objects.filter(pk=quote.pk).update(
            proposal_valid_until=timezone.localdate() - timedelta(days=1)
        )
        with self.assertRaises(BusinessError) as ctx:
            services.accept_quote(quote.reference, quote.access_token)
        self.assertEqual(ctx.exception.code, "proposal_expired")

    def test_client_can_decline(self):
        quote = services.send_proposal(
            self._create(), amount=Decimal("100"), message="…",
            valid_until=timezone.localdate() + timedelta(days=3),
        )
        with self.captureOnCommitCallbacks(execute=True):
            quote = services.decline_quote(quote.reference, quote.access_token, reason="Trop cher")
        self.assertEqual(quote.status, QuoteRequest.Status.REFUSEE)
        self.assertIn("Trop cher", quote.comments)
        # Le commercial est prévenu, avec le motif ; l'email de l'agence permet de répondre au client.
        alert = Notification.objects.get(event=Notification.Event.QUOTE_DECLINED)
        self.assertEqual(alert.recipient, self.commercial)
        self.assertIn("Trop cher", alert.message)
        agency = next(m for m in mail.outbox if m.to == ["contact@agence-voyage.com"])
        self.assertEqual(agency.reply_to, ["awa@example.com"])

    def test_emails_follow_the_client_language(self):
        with self.captureOnCommitCallbacks(execute=True):
            quote = self._create(language="en")
        confirmation = next(m for m in mail.outbox if m.to == [quote.email])
        self.assertEqual(confirmation.subject, f"Your quote request {quote.reference}")
        self.assertIn(f"/en/devis/{quote.reference}?token=", confirmation.body)
        self.assertIn('lang="en"', confirmation.alternatives[0][0])
        with self.captureOnCommitCallbacks(execute=True):
            services.send_proposal(quote, amount=Decimal("1850000"), message="7 nights.",
                                   valid_until=timezone.localdate() + timedelta(days=10))
        self.assertIn("1,850,000 FCFA", mail.outbox[-1].body)
        self.assertIn("Hello Awa,", mail.outbox[-1].body)

    def test_status_path_is_enforced(self):
        with self.assertRaises(InvalidTransition):
            services.change_quote_status(self._create(), QuoteRequest.Status.TERMINEE)


class ContactTests(TestCase):
    def test_contact_message_notifies_staff(self):
        admin = UserFactory(role="ADMIN")
        with self.captureOnCommitCallbacks(execute=True):
            contact = services.create_contact_message(
                name="Yao Koffi", email="yao@example.com", subject="Visa", message="Bonjour…",
                language="en",
            )
        self.assertEqual(contact.status, ContactMessage.Status.NOUVEAU)
        self.assertTrue(Notification.objects.filter(recipient=admin).exists())
        # L'agence peut répondre directement ; le client reçoit un accusé de réception.
        agency = next(m for m in mail.outbox if m.to == ["contact@agence-voyage.com"])
        self.assertEqual(agency.reply_to, ["yao@example.com"])
        acknowledgement = next(m for m in mail.outbox if m.to == ["yao@example.com"])
        self.assertEqual(acknowledgement.subject, "We have received your message")
        self.assertIn("Hello Yao,", acknowledgement.body)
        services.change_contact_status(contact, ContactMessage.Status.TRAITE)
        with self.assertRaises(InvalidTransition):
            services.change_contact_status(contact, ContactMessage.Status.NOUVEAU)
