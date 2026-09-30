from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone, translation
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.accommodations.selectors import hotel_list
from apps.accommodations.serializers import HotelListSerializer
from apps.blog.models import BlogPost
from apps.blog.serializers import BlogPostListSerializer
from apps.core.models import ExchangeRate
from apps.core.tests.factories import (
    ActivityFactory,
    DestinationFactory,
    RoomFactory,
    TourDepartureFactory,
    TourFactory,
    UserFactory,
    VehicleFactory,
)
from apps.destinations.selectors import destination_detail
from apps.destinations.serializers import DestinationDetailSerializer
from apps.offers.models import Offer
from apps.offers.serializers import OfferListSerializer
from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer
from apps.tours.selectors import tour_detail, tour_list
from apps.tours.serializers import TourDetailSerializer, TourListSerializer
from apps.vehicles.serializers import VehicleDetailSerializer


def api_request(path="/", **headers):
    return Request(APIRequestFactory().get(path, **headers))


def in_days(n):
    return timezone.localdate() + timedelta(days=n)


class MoneyAndTranslationTests(TestCase):
    def setUp(self):
        cache.clear()
        ExchangeRate.objects.create(currency="EUR", rate_from_xof=Decimal("1") / Decimal("655.957"))
        self.departure = TourDepartureFactory(start_date=in_days(20), end_date=in_days(22))
        tour = self.departure.tour
        tour.title_fr, tour.title_en = "Découverte d'Abidjan", ""
        tour.inclusions = "Hébergement\n- Guide francophone\n\n"
        tour.save()

    def test_list_in_english_with_euro_display(self):
        request = api_request("/?currency=EUR")
        with translation.override("en"):
            data = TourListSerializer(tour_list(), many=True, context={"request": request}).data
        tour = data[0]
        self.assertEqual(tour["title"], "Découverte d'Abidjan")  # repli sur le français
        self.assertEqual(tour["price"], {
            "amount": "150000.00", "currency": "XOF",
            "display": {"amount": "228.67", "currency": "EUR"},
        })
        self.assertEqual(tour["next_departure"], str(self.departure.start_date))
        self.assertEqual(tour["rating_count"], 0)

    def test_unknown_display_currency_is_ignored(self):
        data = TourListSerializer(
            tour_list(), many=True, context={"request": api_request("/?currency=JPY")}
        ).data
        self.assertNotIn("display", data[0]["price"])

    def test_detail_lists_open_departures_and_inclusions(self):
        TourDepartureFactory(tour=self.departure.tour, start_date=in_days(-5), end_date=in_days(-3))
        data = TourDetailSerializer(
            tour_detail(self.departure.tour.slug), context={"request": api_request()}
        ).data
        self.assertEqual([d["id"] for d in data["departures"]], [self.departure.pk])
        self.assertEqual(data["departures"][0]["seats_left"], 10)
        self.assertEqual(data["inclusions"], ["Hébergement", "Guide francophone"])
        self.assertIsNone(data["promo_price"])
        self.assertEqual(data["rating"], {"average": None, "count": 0})


class ExposureTests(TestCase):
    """Aucune donnée interne ou personnelle dans les réponses publiques."""

    def test_vehicle_plate_is_never_exposed(self):
        data = VehicleDetailSerializer(VehicleFactory(), context={"request": api_request()}).data
        self.assertNotIn("plate_number", data)

    def test_review_and_blog_hide_emails(self):
        review = Review.objects.create(
            author_name="Fatou", author_email="fatou@example.com", rating=5, comment="Top"
        )
        self.assertNotIn("author_email", ReviewSerializer(review).data)
        author = UserFactory(role="AGENT", first_name="Koffi", last_name="N'Guessan")
        post = BlogPost.objects.create(title="T", slug="t", excerpt="E", content="C", author=author)
        data = BlogPostListSerializer(post, context={"request": api_request()}).data
        self.assertEqual(data["author_name"], "Koffi N'Guessan")
        self.assertNotIn(author.email, str(data))


class CatalogRepresentationTests(TestCase):
    def test_hotel_price_from(self):
        RoomFactory(base_price=Decimal("45000"))
        data = HotelListSerializer(hotel_list(), many=True, context={"request": api_request()}).data
        self.assertEqual(data[0]["price_from"], {"amount": "45000.00", "currency": "XOF"})

    def test_offer_badge_discount_and_target(self):
        tour = TourFactory(title="Assinie", slug="assinie")
        offer = Offer.objects.create(
            title="Promo", slug="promo", offer_type=Offer.OfferType.CIRCUIT,
            initial_price=Decimal("200000"), promo_price=Decimal("150000"),
            start_date=in_days(-1), end_date=in_days(5), seats_available=3,
            badge=Offer.Badge.PROMOTION, tour=tour,
        )
        data = OfferListSerializer(offer, context={"request": api_request()}).data
        self.assertEqual(data["discount_percent"], 25)
        self.assertEqual(data["badge"], "DERNIERES_PLACES")
        self.assertEqual(data["target"], {"type": "tour", "slug": "assinie", "title": "Assinie"})

    def test_destination_detail_only_shows_published_content_in_few_queries(self):
        destination = DestinationFactory()
        TourFactory(destination=destination)
        TourFactory(destination=destination, is_published=False)
        ActivityFactory(destination=destination)
        ActivityFactory(destination=destination, is_published=False)
        # Destination, photos, tags, circuits, hôtels, résidences, activités et note des
        # avis : 8 requêtes, quel que soit le nombre de contenus liés.
        with self.assertNumQueries(8):
            data = DestinationDetailSerializer(
                destination_detail(destination.slug), context={"request": api_request()}
            ).data
        self.assertEqual(len(data["tours"]), 1)
        self.assertEqual(len(data["activities"]), 1)
