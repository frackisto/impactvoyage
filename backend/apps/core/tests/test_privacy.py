"""Données personnelles (Phase 23) : export, effacement, durées de conservation."""
import json
from datetime import timedelta
from io import StringIO

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.core import privacy
from apps.inquiries.models import ContactMessage, QuoteRequest
from apps.notifications.models import Notification
from apps.reviews.models import Review

from .factories import (
    BookingFactory,
    BookingItemFactory,
    ContactMessageFactory,
    NotificationFactory,
    QuoteRequestFactory,
    ReviewFactory,
    UserFactory,
)

EMAIL = "awa@example.com"


def age(obj, days, field="updated_at"):
    """Vieillit un enregistrement (update : pas de mise à jour automatique des dates)."""
    type(obj)._base_manager.filter(pk=obj.pk).update(
        **{field: timezone.now() - timedelta(days=days)})


class PersonalDataTests(TestCase):
    def setUp(self):
        self.account = UserFactory(email=EMAIL, first_name="Awa", phone="+2250700000000")
        self.quote = QuoteRequestFactory(email="Awa@Example.com", comments="Chambre pour 2")
        self.quote_booked = QuoteRequestFactory(email=EMAIL)
        self.confirmed = BookingFactory(contact_email=EMAIL, status=Booking.Status.CONFIRMED,
                                        quote=self.quote_booked)
        self.cancelled = BookingFactory(contact_email=EMAIL, status=Booking.Status.CANCELLED,
                                        customer_comments="Mon numéro de passeport…")
        BookingItemFactory(booking=self.cancelled, pickup_location="Villa 12, Cocody")
        self.message = ContactMessageFactory(email=EMAIL)
        self.review = ReviewFactory(author_email=EMAIL)
        self.other = ContactMessageFactory(email="autre@example.com")
        self.notification = NotificationFactory(
            recipient=UserFactory(role=User.Role.AGENT), message="Awa : chambre pour 2",
            content_type=ContentType.objects.get_for_model(ContactMessage),
            object_id=self.message.pk,
        )

    def test_export_gathers_everything_about_an_email(self):
        data = privacy.export_personal_data(EMAIL)["data"]
        self.assertEqual(set(data), {"Compte", "Demandes de devis", "Réservations",
                                     "Messages de contact", "Avis"})
        self.assertEqual(len(data["Demandes de devis"]), 2)  # adresse insensible à la casse
        self.assertEqual(data["Réservations"][1]["prestations"][0]["prise_en_charge"],
                         "Villa 12, Cocody")
        json.dumps(data)  # sérialisable tel quel

    def test_erasure_keeps_accounting_records_and_anonymizes_the_rest(self):
        decisions = {record.obj: record.decision
                     for _, records in privacy.find_personal_data(EMAIL) for record in records}
        self.assertEqual(decisions[self.confirmed], privacy.KEEP)
        self.assertEqual(decisions[self.quote_booked], privacy.KEEP)
        self.assertEqual(decisions[self.cancelled], privacy.ANONYMIZE)

        privacy.erase_personal_data(EMAIL)

        self.quote.refresh_from_db()
        self.assertEqual((self.quote.first_name, self.quote.email, self.quote.comments),
                         (privacy.ANONYMOUS, "", ""))
        self.assertEqual(self.quote.destination_text, "Dubaï")  # statistiques préservées
        self.cancelled.refresh_from_db()
        self.assertEqual((self.cancelled.contact_email, self.cancelled.customer_comments), ("", ""))
        self.assertEqual(self.cancelled.items.get().pickup_location, "")
        self.confirmed.refresh_from_db()
        self.assertEqual(self.confirmed.contact_email, EMAIL)

        self.account.refresh_from_db()
        self.assertFalse(self.account.is_active)
        self.assertFalse(self.account.has_usable_password())
        self.assertEqual(self.account.first_name, "")
        self.assertTrue(self.account.email.endswith("@anonyme.invalid"))

        self.assertFalse(ContactMessage.objects.filter(pk=self.message.pk).exists())
        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())
        self.assertFalse(Notification.objects.filter(pk=self.notification.pk).exists())
        self.assertTrue(ContactMessage.objects.filter(pk=self.other.pk).exists())
        # Plus rien à effacer, hors ce qui est conservé.
        remaining = privacy.find_personal_data(EMAIL)
        self.assertEqual([label for label, _ in remaining], ["Demandes de devis", "Réservations"])

    def test_staff_accounts_are_never_erased(self):
        agent = UserFactory(role=User.Role.AGENT, email="agent@example.com")
        privacy.erase_personal_data("agent@example.com")
        agent.refresh_from_db()
        self.assertTrue(agent.is_active)


class RetentionTests(TestCase):
    def test_expired_data_is_deleted_or_anonymized(self):
        old_message = ContactMessageFactory()
        age(old_message, 2 * 365 + 1, "created_at")
        recent_message = ContactMessageFactory()
        old_quote = QuoteRequestFactory()
        age(old_quote, 3 * 365 + 1)
        old_booked_quote = QuoteRequestFactory()
        age(old_booked_quote, 3 * 365 + 1)
        BookingFactory(quote=old_booked_quote, status=Booking.Status.CONFIRMED)
        old_cancelled = BookingFactory(status=Booking.Status.CANCELLED)
        age(old_cancelled, 3 * 365 + 1)
        old_completed = BookingFactory(status=Booking.Status.COMPLETED)
        age(old_completed, 3 * 365 + 1)  # pièce comptable : 10 ans
        rejected = ReviewFactory(status=Review.Status.REFUSE)
        age(rejected, 366)
        approved = ReviewFactory(status=Review.Status.APPROUVE)
        age(approved, 366)
        old_notification = NotificationFactory(recipient=UserFactory(role=User.Role.AGENT))
        age(old_notification, 366, "created_at")

        report = privacy.apply_retention()

        self.assertEqual(report, {"Messages de contact": 1, "Demandes de devis": 1,
                                  "Réservations": 1, "Avis": 1,
                                  "Notifications de l'équipe": 1})
        self.assertEqual(list(ContactMessage.objects.all()), [recent_message])
        self.assertEqual(QuoteRequest.objects.get(pk=old_quote.pk).email, "")
        self.assertNotEqual(QuoteRequest.objects.get(pk=old_booked_quote.pk).email, "")
        self.assertEqual(Booking.objects.get(pk=old_cancelled.pk).contact_email, "")
        self.assertNotEqual(Booking.objects.get(pk=old_completed.pk).contact_email, "")
        self.assertEqual(list(Review.objects.all()), [approved])
        self.assertEqual(privacy.apply_retention(), {})  # rien à refaire

    def test_command_reports_what_was_done(self):
        age(ContactMessageFactory(), 800, "created_at")
        out = StringIO()
        call_command("apply_retention", stdout=out)
        self.assertIn("Messages de contact : 1", out.getvalue())


class PersonalDataAdminTests(TestCase):
    def setUp(self):
        self.url = reverse("admin:accounts_user_personal_data")
        ContactMessageFactory(email=EMAIL)
        self.quote = QuoteRequestFactory(email=EMAIL)

    def test_admin_searches_exports_then_erases(self):
        self.client.force_login(UserFactory(role=User.Role.ADMIN))
        self.assertEqual(self.client.get(self.url).status_code, 200)

        page = self.client.post(self.url, {"email": EMAIL, "step": "search"})
        self.assertContains(page, self.quote.reference)
        self.assertContains(page, "Sera anonymisé")

        export = self.client.post(self.url, {"email": EMAIL, "step": "export"})
        self.assertIn("attachment", export["Content-Disposition"])
        self.assertEqual(len(json.loads(export.content)["data"]["Messages de contact"]), 1)

        unconfirmed = self.client.post(self.url, {"email": EMAIL, "step": "erase"})
        self.assertContains(unconfirmed, "Cochez la case")
        self.assertTrue(ContactMessage.objects.exists())

        done = self.client.post(self.url, {"email": EMAIL, "step": "erase", "confirm": "on"})
        self.assertContains(done, "Bilan de l")
        self.assertFalse(ContactMessage.objects.exists())

    def test_only_administrators_can_use_it(self):
        self.client.force_login(UserFactory(role=User.Role.COMMERCIAL))
        response = self.client.post(self.url, {"email": EMAIL, "step": "erase", "confirm": "on"})
        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(ContactMessage.objects.exists())
