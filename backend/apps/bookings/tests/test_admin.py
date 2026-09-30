from datetime import timedelta
from unittest import mock

from django.contrib import admin
from django.core import mail
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import Booking
from apps.core.tests.admin_helpers import AdminTestCase
from apps.core.tests.factories import (
    BookingFactory,
    BookingItemFactory,
    UserFactory,
    VehicleFactory,
)

Status = Booking.Status


class BookingAdminTests(AdminTestCase):
    def setUp(self):
        self.vehicle = VehicleFactory()
        self.start = timezone.localdate() + timedelta(days=10)
        self.booking = self.request_vehicle()

    def request_vehicle(self):
        booking = BookingFactory(status=Status.REQUESTED, total_amount=self.vehicle.base_price * 3)
        BookingItemFactory(booking=booking, vehicle=self.vehicle, start_date=self.start,
                           end_date=self.start + timedelta(days=3), is_blocking=False)
        return booking

    def url(self, name, booking=None):
        return reverse(f"admin:bookings_booking_{name}", args=[(booking or self.booking).pk])

    def detail_actions(self, response):
        return [a["path"] for a in response.context["actions_detail"]]

    def test_confirmation_asks_first_then_blocks_the_stock_and_emails_the_client(self):
        self.login("COMMERCIAL")
        response = self.client.get(self.url("confirm_detail"))
        self.assertTemplateUsed(response, "admin/decision_form.html")
        self.assertContains(response, "Confirmer la réservation")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Status.REQUESTED)  # un GET ne change rien

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url("confirm_detail"), {"reason": "Acompte reçu"})
        self.assertRedirects(response, self.url("change"))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Status.CONFIRMED)
        self.assertEqual(self.booking.internal_notes, "Acompte reçu")
        self.assertTrue(self.booking.items.get().is_blocking)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Réservation confirmée", mail.outbox[0].subject)

    def test_confirmation_refused_when_the_vehicle_was_taken_meanwhile(self):
        other = self.request_vehicle()
        self.login("COMMERCIAL")
        self.client.post(self.url("confirm_detail", other), {"reason": ""})
        response = self.client.post(self.url("confirm_detail"), {"reason": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "déjà réservé sur ces dates")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Status.REQUESTED)

    def test_reject_with_a_reason(self):
        self.login("COMMERCIAL")
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url("reject_detail"), {"reason": "Véhicule en révision"})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Status.REJECTED)
        self.assertIn("Véhicule en révision", self.booking.internal_notes)
        self.assertIn("Véhicule en révision", mail.outbox[-1].body)

    def test_cancelling_a_confirmed_booking_releases_the_stock(self):
        self.login("COMMERCIAL")
        self.client.post(self.url("confirm_detail"), {"reason": ""})
        self.client.post(self.url("cancel_detail"), {"reason": "Client malade"})
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Status.CANCELLED)
        self.assertFalse(self.booking.items.get().is_blocking)

    def test_only_the_decisions_allowed_by_the_status_are_offered(self):
        self.login("COMMERCIAL")
        paths = self.detail_actions(self.client.get(self.url("change")))
        self.assertEqual(sorted(paths), sorted([self.url(n) for n in
                                                ("confirm_detail", "reject_detail", "cancel_detail")]))

        self.client.post(self.url("confirm_detail"), {"reason": ""})
        paths = self.detail_actions(self.client.get(self.url("change")))
        self.assertEqual(paths, [self.url("cancel_detail")])
        self.assertEqual(self.client.post(self.url("reject_detail"), {"reason": ""}).status_code, 403)

    def test_malformed_identifier_is_refused_cleanly(self):
        self.login("COMMERCIAL")
        url = reverse("admin:bookings_booking_changelist") + "abc/change/confirm/"
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_manager_sees_bookings_but_cannot_decide(self):
        self.login("GESTIONNAIRE")
        response = self.client.get(self.url("change"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.detail_actions(response), [])
        self.assertEqual(self.client.post(self.url("confirm_detail"), {}).status_code, 403)

    def test_agent_has_no_access_to_bookings(self):
        self.login("AGENT")
        response = self.client.get(reverse("admin:bookings_booking_changelist"))
        self.assertEqual(response.status_code, 403)

    def test_saving_notes_never_overwrites_a_status_changed_meanwhile(self):
        commercial = UserFactory(role="COMMERCIAL")
        stale = Booking.objects.get(pk=self.booking.pk)
        Booking.objects.filter(pk=self.booking.pk).update(status=Status.CANCELLED)  # le client annule
        stale.internal_notes = "Rappeler le client"
        request = RequestFactory().post("/")
        request.user = commercial
        admin.site._registry[Booking].save_model(
            request, stale, mock.Mock(changed_data=["internal_notes"]), change=True)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Status.CANCELLED)
        self.assertEqual(self.booking.internal_notes, "Rappeler le client")

    def test_saving_the_form_only_updates_internal_notes(self):
        self.login("COMMERCIAL")
        url = self.url("change")
        response = self.client.get(url)
        form = response.context["adminform"].form
        self.assertEqual(list(form.fields), ["internal_notes"])
        data = {"internal_notes": "Préférence : siège bébé", "_save": "",
                "items-TOTAL_FORMS": "1", "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0", "items-MAX_NUM_FORMS": "1000",
                "items-0-id": str(self.booking.items.get().pk),
                "items-0-booking": str(self.booking.pk)}
        self.assertRedirects(self.client.post(url, data), reverse("admin:bookings_booking_changelist"))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.internal_notes, "Préférence : siège bébé")
        self.assertEqual(self.booking.status, Status.REQUESTED)

    def test_a_booking_holding_stock_cannot_be_deleted(self):
        self.login("ADMIN")
        self.client.post(self.url("confirm_detail"), {"reason": ""})
        self.assertEqual(self.client.get(self.url("delete")).status_code, 403)

        response = self.client.post(reverse("admin:bookings_booking_changelist"), {
            "action": "delete_selected", "_selected_action": [self.booking.pk], "post": "yes",
        })
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Booking.objects.filter(pk=self.booking.pk).exists())

    def test_deleting_a_finished_request_is_a_soft_delete(self):
        self.login("ADMIN")
        self.client.post(self.url("reject_detail"), {"reason": ""})
        self.client.post(reverse("admin:bookings_booking_changelist"), {
            "action": "delete_selected", "_selected_action": [self.booking.pk], "post": "yes",
        })
        self.assertFalse(Booking.objects.filter(pk=self.booking.pk).exists())
        self.assertIsNotNone(Booking.all_objects.get(pk=self.booking.pk).deleted_at)
