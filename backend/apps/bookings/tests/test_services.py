import threading
import uuid
from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.bookings import services
from apps.bookings.models import Booking
from apps.bookings.services import ItemRequest
from apps.core.exceptions import BusinessError, InvalidToken, InvalidTransition, NotAvailable
from apps.core.models import BookableMixin
from apps.core.tests.helpers import (
    make_activity,
    make_departure,
    make_residence,
    make_room,
    make_user,
    make_vehicle,
)
from apps.notifications.models import Notification
from apps.offers.models import Offer
from apps.tours.models import TourDeparture

CONTACT = {
    "contact_name": "Awa Koné",
    "contact_email": "awa@example.com",
    "contact_phone": "+2250700000000",
}


def in_days(n):
    return timezone.localdate() + timedelta(days=n)


def request(*items, **kwargs):
    return services.request_booking(**CONTACT, items=list(items), **kwargs)


class RequestBookingTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMIN")
        self.commercial = make_user("COMMERCIAL")
        self.departure = make_departure(start_date=in_days(30), end_date=in_days(33), capacity=10)

    def test_request_is_priced_server_side_and_blocks_nothing(self):
        with self.captureOnCommitCallbacks(execute=True):
            booking = request(ItemRequest("tour_departure", self.departure.pk, quantity=2))

        self.assertEqual(booking.status, Booking.Status.REQUESTED)
        self.assertEqual(booking.total_amount, Decimal("300000"))
        item = booking.items.get()
        self.assertEqual(item.unit_price, Decimal("150000"))
        self.assertFalse(item.is_blocking)
        self.departure.refresh_from_db()
        self.assertEqual(self.departure.seats_reserved, 0)

        # Notification tableau de bord pour l'admin et le commercial, emails agence + client.
        self.assertEqual(
            set(Notification.objects.values_list("recipient", flat=True)),
            {self.admin.pk, self.commercial.pk},
        )
        self.assertEqual(
            sorted(m.to[0] for m in mail.outbox),
            ["awa@example.com", "contact@agence-voyage.com"],
        )

    def test_active_offer_lowers_the_unit_price(self):
        Offer.objects.create(
            title="Promo", slug="promo", offer_type=Offer.OfferType.CIRCUIT,
            initial_price=Decimal("150000"), promo_price=Decimal("120000"),
            start_date=in_days(-1), end_date=in_days(10), tour=self.departure.tour,
        )
        booking = request(ItemRequest("tour_departure", self.departure.pk, quantity=1))
        self.assertEqual(booking.total_amount, Decimal("120000"))

    def test_more_travelers_than_seats_is_refused(self):
        with self.assertRaises(NotAvailable):
            request(ItemRequest("tour_departure", self.departure.pk, quantity=11))

    def test_past_dates_and_unknown_offers_are_refused(self):
        vehicle = make_vehicle()
        with self.assertRaises(BusinessError):
            request(ItemRequest("vehicle", vehicle.pk, in_days(-2), in_days(1)))
        with self.assertRaises(BusinessError):
            request(ItemRequest("vehicle", 999999, in_days(2), in_days(4)))
        with self.assertRaises(BusinessError):
            request()

    def test_vehicle_is_priced_per_day(self):
        vehicle = make_vehicle(base_price=Decimal("60000"))
        booking = request(
            ItemRequest("vehicle", vehicle.pk, in_days(5), in_days(8), pickup_location="Aéroport")
        )
        item = booking.items.get()
        self.assertEqual(item.line_total, Decimal("180000"))
        self.assertEqual(item.pickup_location, "Aéroport")


class LifecycleTests(TestCase):
    def setUp(self):
        self.departure = make_departure(start_date=in_days(30), end_date=in_days(33), capacity=10)

    def _tour_request(self, travelers):
        return request(ItemRequest("tour_departure", self.departure.pk, quantity=travelers))

    def test_confirmation_reserves_seats_and_fills_the_departure(self):
        booking = services.confirm_booking(self._tour_request(10))
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertTrue(booking.items.get().is_blocking)
        self.departure.refresh_from_db()
        self.assertEqual(self.departure.seats_reserved, 10)
        self.assertEqual(self.departure.status, TourDeparture.Status.FULL)

    def test_second_confirmation_beyond_capacity_is_refused(self):
        first, second = self._tour_request(6), self._tour_request(6)
        services.confirm_booking(first)
        with self.assertRaises(NotAvailable):
            services.confirm_booking(second)
        second.refresh_from_db()
        self.departure.refresh_from_db()
        self.assertEqual(second.status, Booking.Status.REQUESTED)
        self.assertEqual(self.departure.seats_reserved, 6)

    def test_cancellation_releases_seats_and_reopens(self):
        booking = services.confirm_booking(self._tour_request(10))
        services.cancel_booking(booking, reason="Changement de programme")
        self.departure.refresh_from_db()
        self.assertEqual(self.departure.seats_reserved, 0)
        self.assertEqual(self.departure.status, TourDeparture.Status.OPEN)
        self.assertFalse(booking.items.get().is_blocking)

    def test_customer_cancels_only_before_confirmation(self):
        request_ = self._tour_request(2)
        with self.captureOnCommitCallbacks(execute=True):
            services.cancel_booking(request_, reason="Imprévu", by_customer=True)
        request_.refresh_from_db()
        self.assertEqual(request_.status, Booking.Status.CANCELLED)
        self.assertTrue(any(services.client_booking_url(request_) in m.body for m in mail.outbox))

        confirmed = services.confirm_booking(self._tour_request(2))
        with self.assertRaises(InvalidTransition) as ctx:
            services.cancel_booking(confirmed, by_customer=True)
        self.assertEqual(ctx.exception.code, "contact_agency")
        confirmed.refresh_from_db()
        self.assertEqual(confirmed.status, Booking.Status.CONFIRMED)

    def test_client_link_gives_access_with_the_right_token_only(self):
        booking = self._tour_request(2)
        self.assertEqual(services.get_booking_for_client(booking.reference, booking.access_token), booking)
        for token in ("", "abc", uuid.uuid4()):
            with self.assertRaises(InvalidToken):
                services.get_booking_for_client(booking.reference, token)

    def test_rejection_and_forbidden_transitions(self):
        booking = services.reject_booking(self._tour_request(2), reason="Complet")
        self.assertEqual(booking.status, Booking.Status.REJECTED)
        with self.assertRaises(InvalidTransition):
            services.confirm_booking(booking)

    def test_instant_booking_blocks_then_expires(self):
        tour = self.departure.tour
        tour.booking_mode = BookableMixin.BookingMode.INSTANT
        tour.save()
        booking = self._tour_request(4)
        self.assertEqual(booking.status, Booking.Status.PENDING)
        self.departure.refresh_from_db()
        self.assertEqual(self.departure.seats_reserved, 4)

        self.assertEqual(services.expire_pending_bookings(now=timezone.now()), 0)
        later = timezone.now() + timedelta(minutes=31)
        self.assertEqual(services.expire_pending_bookings(now=later), 1)
        booking.refresh_from_db()
        self.departure.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)
        self.assertEqual(self.departure.seats_reserved, 0)

    def test_complete_past_bookings(self):
        booking = services.confirm_booking(self._tour_request(1))
        self.assertEqual(services.complete_past_bookings(today=in_days(20)), 0)
        self.assertEqual(services.complete_past_bookings(today=in_days(40)), 1)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.COMPLETED)


class OtherStockTests(TestCase):
    def test_vehicle_double_booking(self):
        vehicle = make_vehicle()
        first = request(ItemRequest("vehicle", vehicle.pk, in_days(10), in_days(14)))
        second = request(ItemRequest("vehicle", vehicle.pk, in_days(12), in_days(16)))
        services.confirm_booking(first)
        with self.assertRaises(NotAvailable):
            services.confirm_booking(second)
        # Une nouvelle demande sur ces dates est refusée d'emblée.
        with self.assertRaises(NotAvailable):
            request(ItemRequest("vehicle", vehicle.pk, in_days(13), in_days(15)))
        # Location suivante, au jour de restitution : acceptée.
        services.confirm_booking(
            request(ItemRequest("vehicle", vehicle.pk, in_days(14), in_days(16)))
        )

    def test_room_quantity(self):
        room = make_room(quantity=1)
        first = request(ItemRequest("room", room.pk, in_days(10), in_days(12)))
        second = request(ItemRequest("room", room.pk, in_days(11), in_days(13)))
        self.assertEqual(first.total_amount, Decimal("90000"))
        services.confirm_booking(first)
        with self.assertRaises(NotAvailable):
            services.confirm_booking(second)

    def test_residence_overlap(self):
        residence = make_residence()
        services.confirm_booking(
            request(ItemRequest("residence", residence.pk, in_days(10), in_days(15)))
        )
        with self.assertRaises(NotAvailable):
            request(ItemRequest("residence", residence.pk, in_days(14), in_days(16)))

    def test_activity_places_per_day(self):
        activity = make_activity(max_participants=5)
        services.confirm_booking(
            request(ItemRequest("activity", activity.pk, in_days(7), quantity=4))
        )
        with self.assertRaises(NotAvailable):
            request(ItemRequest("activity", activity.pk, in_days(7), quantity=2))
        request(ItemRequest("activity", activity.pk, in_days(8), quantity=2))


class ConcurrentConfirmationTests(TransactionTestCase):
    """Deux commerciaux confirment en même temps deux demandes pour la dernière place."""

    def test_only_one_confirmation_wins(self):
        departure = make_departure(start_date=in_days(30), end_date=in_days(33), capacity=1)
        bookings = [
            request(ItemRequest("tour_departure", departure.pk, quantity=1)) for _ in range(2)
        ]
        results = []
        barrier = threading.Barrier(2)

        def confirm(booking):
            barrier.wait()
            try:
                services.confirm_booking(booking)
                results.append("ok")
            except NotAvailable:
                results.append("refusé")
            finally:
                connection.close()

        threads = [threading.Thread(target=confirm, args=(b,)) for b in bookings]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(sorted(results), ["ok", "refusé"])
        departure.refresh_from_db()
        self.assertEqual(departure.seats_reserved, 1)
