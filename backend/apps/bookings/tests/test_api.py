import uuid
from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.utils import timezone

from apps.bookings.models import Booking
from apps.core.tests.helpers import make_departure, make_tour, make_user, make_vehicle
from apps.core.tests.test_api import API, ApiTestCase
from apps.inquiries.models import QuoteRequest
from apps.notifications.models import Notification
from apps.reviews.models import Review


def in_days(n):
    return timezone.localdate() + timedelta(days=n)


CONTACT = {"contact_name": "Awa Koné", "contact_email": "awa@example.com",
           "contact_phone": "+2250700000000", "consent": True}


class BookingApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.staff = make_user("COMMERCIAL")
        self.client_user = make_user("CLIENT")
        self.departure = make_departure(start_date=in_days(30), end_date=in_days(33), capacity=4)

    def _request(self, travelers=2, **extra):
        return self.client.post(f"{API}/bookings/", {**CONTACT, "items": [
            {"kind": "tour_departure", "object_id": self.departure.pk, "quantity": travelers}
        ], **extra}, format="json")

    def test_guest_request_then_staff_confirmation(self):
        response = self._request()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "REQUESTED")
        self.assertEqual(response.data["total_amount"]["amount"], "300000.00")
        reference = response.data["reference"]

        # Un anonyme ou un client ne peut ni lister toutes les réservations ni confirmer.
        self.assertEqual(self.client.get(f"{API}/bookings/").status_code, 401)
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.client.post(f"{API}/bookings/{reference}/confirm/").status_code, 403)
        self.assertEqual(self.client.get(f"{API}/bookings/{reference}/").status_code, 404)

        self.client.force_authenticate(self.staff)
        confirmed = self.client.post(f"{API}/bookings/{reference}/confirm/", {"reason": "OK"})
        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(confirmed.data["status"], "CONFIRMED")
        self.assertIn("internal_notes", confirmed.data)

    def test_business_errors_use_the_error_format(self):
        response = self._request(travelers=5)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"]["code"], "not_available")
        self.assertEqual(response.data["error"]["details"], {"seats_left": 4})

        reference = self._request().data["reference"]
        self.client.force_authenticate(self.staff)
        self.client.post(f"{API}/bookings/{reference}/reject/")
        again = self.client.post(f"{API}/bookings/{reference}/confirm/")
        self.assertEqual(again.status_code, 409)
        self.assertEqual(again.data["error"]["code"], "invalid_transition")

    def test_client_sees_and_cancels_own_request_only_before_confirmation(self):
        self.client.force_authenticate(self.client_user)
        reference = self._request().data["reference"]
        self.assertEqual(Booking.objects.get(reference=reference).user, self.client_user)
        self.assertEqual(self.client.get(f"{API}/bookings/").data["count"], 1)
        self.assertNotIn("internal_notes", self.client.get(f"{API}/bookings/{reference}/").data)

        second = self._request().data["reference"]
        self.client.force_authenticate(self.staff)
        self.client.post(f"{API}/bookings/{second}/confirm/")
        self.client.force_authenticate(self.client_user)
        refused = self.client.post(f"{API}/bookings/{second}/cancel/")
        self.assertEqual((refused.status_code, refused.data["error"]["code"]), (409, "contact_agency"))
        cancelled = self.client.post(f"{API}/bookings/{reference}/cancel/", {"reason": "Imprévu"})
        self.assertEqual(cancelled.data["status"], "CANCELLED")

    def test_prices_sent_by_the_client_are_ignored(self):
        vehicle = make_vehicle(base_price=Decimal("60000"))
        response = self.client.post(f"{API}/bookings/", {**CONTACT, "items": [
            {"kind": "vehicle", "object_id": vehicle.pk, "start_date": str(in_days(2)),
             "end_date": str(in_days(4)), "unit_price": "1", "line_total": "1"}
        ], "total_amount": "1"}, format="json")
        self.assertEqual(response.data["total_amount"]["amount"], "120000.00")

    def test_consent_is_required(self):
        response = self._request(consent=False)
        self.assertEqual(response.status_code, 400)
        self.assertIn("consent", response.data["error"]["details"])
        self.assertFalse(Booking.objects.exists())
        self._request()
        self.assertIsNotNone(Booking.objects.get().consent_at)

    def test_guest_tracks_and_cancels_with_the_link_token(self):
        with self.captureOnCommitCallbacks(execute=True):
            created = self._request()
        reference, token = created.data["reference"], created.data["access_token"]
        booking = Booking.objects.get(reference=reference)
        self.assertEqual(token, str(booking.access_token))
        self.assertTrue(created.data["can_cancel"])
        self.assertEqual(created.data["items"][0]["target_slug"], self.departure.tour.slug)
        # Le lien de suivi figure dans l'email de confirmation.
        self.assertTrue(any(f"/reservation/{reference}?token={token}" in m.body for m in mail.outbox))

        tracked = self.client.get(f"{API}/bookings/{reference}/", {"token": token})
        self.assertEqual(tracked.status_code, 200)
        self.assertEqual(tracked.data["status"], "REQUESTED")
        self.assertNotIn("access_token", tracked.data)
        self.assertNotIn("internal_notes", tracked.data)

        # Jeton faux, mal formé ou d'une autre réservation : même réponse, sans fuite.
        other = self._request().data
        for bad in ("pas-un-uuid", str(uuid.uuid4()), other["access_token"]):
            response = self.client.get(f"{API}/bookings/{reference}/", {"token": bad})
            self.assertEqual((response.status_code, response.data["error"]["code"]), (404, "invalid_token"))
        self.assertEqual(
            self.client.post(f"{API}/bookings/{reference}/cancel/", {"token": other["access_token"]}).status_code,
            404,
        )

        cancelled = self.client.post(f"{API}/bookings/{reference}/cancel/", {"token": token, "reason": "Imprévu"})
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.data["status"], "CANCELLED")
        self.assertFalse(cancelled.data["can_cancel"])
        self.assertTrue(Notification.objects.filter(event=Notification.Event.BOOKING_CANCELLED).exists())

    def test_guest_cannot_cancel_a_confirmed_booking(self):
        created = self._request().data
        self.client.force_authenticate(self.staff)
        self.client.post(f"{API}/bookings/{created['reference']}/confirm/")
        self.client.force_authenticate(None)
        tracked = self.client.get(f"{API}/bookings/{created['reference']}/", {"token": created["access_token"]})
        self.assertEqual(tracked.data["status"], "CONFIRMED")
        self.assertFalse(tracked.data["can_cancel"])
        response = self.client.post(
            f"{API}/bookings/{created['reference']}/cancel/", {"token": created["access_token"]}
        )
        self.assertEqual((response.status_code, response.data["error"]["code"]), (409, "contact_agency"))
        # Sans jeton ni compte : authentification requise.
        self.assertEqual(self.client.get(f"{API}/bookings/{created['reference']}/").status_code, 401)
        self.assertEqual(self.client.post(f"{API}/bookings/{created['reference']}/cancel/").status_code, 401)


class QuoteApiTests(ApiTestCase):
    QUOTE = {"first_name": "Awa", "last_name": "Koné", "email": "awa@example.com",
             "phone": "+2250700000000", "destination_text": "Zanzibar", "consent": True}

    def test_full_quote_flow_over_the_api(self):
        commercial = make_user("COMMERCIAL")
        created = self.client.post(f"{API}/quotes/", self.QUOTE, format="json")
        self.assertEqual(created.status_code, 201)
        reference = created.data["reference"]
        self.assertNotIn("access_token", created.data)
        self.assertEqual(Notification.objects.filter(recipient=commercial).count(), 1)

        # Sans jeton valide, le client ne voit rien.
        self.assertEqual(self.client.get(f"{API}/quotes/{reference}/").status_code, 404)
        self.assertEqual(self.client.get(f"{API}/quotes/{reference}/?token=abc").status_code, 404)
        self.assertEqual(self.client.get(f"{API}/quotes/").status_code, 401)

        self.client.force_authenticate(commercial)
        sent = self.client.post(f"{API}/quotes/{reference}/send-proposal/", {
            "amount": "1850000", "message": "7 nuits tout compris.",
            "valid_until": str(in_days(10)),
        })
        self.assertEqual(sent.data["status"], "DEVIS_ENVOYE")
        self.assertNotIn("access_token", sent.data)
        self.client.force_authenticate(None)

        token = str(QuoteRequest.objects.get(reference=reference).access_token)
        seen = self.client.get(f"{API}/quotes/{reference}/", {"token": token})
        self.assertTrue(seen.data["can_answer"])
        self.assertEqual(seen.data["destination_label"], "Zanzibar")  # destination libre
        self.assertEqual(seen.data["proposal_amount"]["amount"], "1850000.00")

        accepted = self.client.post(f"{API}/quotes/{reference}/accept/", {"token": token})
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.data["status"], "PENDING")

    def test_consent_is_required(self):
        response = self.client.post(f"{API}/quotes/", {**self.QUOTE, "consent": False},
                                    format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("consent", response.data["error"]["details"])


class ReviewApiTests(ApiTestCase):
    def test_submit_then_only_approved_reviews_are_listed(self):
        tour = make_tour()
        response = self.client.post(f"{API}/reviews/", {
            "author_name": "Fatou", "author_email": "f@example.com", "rating": 5,
            "comment": "Un circuit inoubliable !", "target_type": "tour",
            "target_slug": tour.slug,
        })
        self.assertEqual(response.status_code, 201)
        url = f"{API}/reviews/?target_type=tour&target_slug={tour.slug}"
        self.assertEqual(self.client.get(url).data["count"], 0)
        Review.objects.update(status=Review.Status.APPROUVE)
        listed = self.client.get(url).data["results"]
        self.assertEqual(len(listed), 1)
        self.assertNotIn("author_email", listed[0])


class NotificationApiTests(ApiTestCase):
    def test_staff_reads_own_notifications(self):
        admin = make_user("ADMIN")
        self.client.post(f"{API}/contact/", {"name": "Yao", "email": "y@example.com",
                                            "subject": "Info", "message": "Bonjour à vous !"})
        self.assertEqual(self.client.get(f"{API}/notifications/").status_code, 401)
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get(f"{API}/notifications/unread-count/").data["count"], 1)
        notification = self.client.get(f"{API}/notifications/?unread=true").data["results"][0]
        self.client.post(f"{API}/notifications/{notification['id']}/read/")
        self.assertEqual(self.client.get(f"{API}/notifications/unread-count/").data["count"], 0)

        self.client.force_authenticate(make_user("CLIENT"))
        self.assertEqual(self.client.get(f"{API}/notifications/").status_code, 403)
