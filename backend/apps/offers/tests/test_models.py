from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.core.tests.helpers import make_tour, make_vehicle
from apps.offers.models import Offer


def make_offer(**kwargs):
    today = timezone.localdate()
    defaults = {
        "title": "Offre",
        "slug": f"offre-{Offer.objects.count() + 1}",
        "offer_type": Offer.OfferType.CIRCUIT,
        "initial_price": Decimal("200000"),
        "promo_price": Decimal("150000"),
        "start_date": today - timedelta(days=1),
        "end_date": today + timedelta(days=10),
    }
    return Offer.objects.create(**{**defaults, **kwargs})


class OfferTests(TestCase):
    def test_discount_percent_is_computed(self):
        self.assertEqual(make_offer().discount_percent, 25)

    def test_promo_price_must_be_below_initial_price(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_offer(promo_price=Decimal("200000"))

    def test_offer_has_at_most_one_target(self):
        make_offer(tour=make_tour())
        make_offer(offer_type=Offer.OfferType.BILLET)
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_offer(tour=make_tour(), vehicle=make_vehicle())

    def test_currently_active(self):
        active = make_offer()
        make_offer(is_active=False)
        make_offer(
            start_date=timezone.localdate() + timedelta(days=5),
            end_date=timezone.localdate() + timedelta(days=9),
        )
        self.assertEqual(list(Offer.objects.currently_active()), [active])
