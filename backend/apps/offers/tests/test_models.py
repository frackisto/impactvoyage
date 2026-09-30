from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.core.tests.factories import OfferFactory, TourFactory, VehicleFactory
from apps.offers.models import Offer


class OfferTests(TestCase):
    def test_discount_percent_is_computed(self):
        self.assertEqual(OfferFactory().discount_percent, 25)

    def test_promo_price_must_be_below_initial_price(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            OfferFactory(promo_price=Decimal("200000"))

    def test_offer_has_at_most_one_target(self):
        OfferFactory(tour=TourFactory())
        OfferFactory(offer_type=Offer.OfferType.BILLET)
        with self.assertRaises(IntegrityError), transaction.atomic():
            OfferFactory(tour=TourFactory(), vehicle=VehicleFactory())

    def test_currently_active(self):
        active = OfferFactory()
        OfferFactory(is_active=False)
        OfferFactory(
            start_date=timezone.localdate() + timedelta(days=5),
            end_date=timezone.localdate() + timedelta(days=9),
        )
        self.assertEqual(list(Offer.objects.currently_active()), [active])
