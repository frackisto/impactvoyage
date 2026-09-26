from apps.core.tests.helpers import make_activity, make_destination, make_residence, make_tour
from apps.core.tests.test_api import API, ApiTestCase
from apps.destinations.models import Destination
from apps.reviews.models import Review


class DestinationApiTests(ApiTestCase):
    def test_list_filters_by_continent_and_country(self):
        make_destination(country_code="CI")
        make_destination(country_code="FR", continent=Destination.Continent.EUROPE)
        make_destination(country_code="AE", continent=Destination.Continent.MOYEN_ORIENT)
        make_destination(country_code="FR", is_published=False)

        url = f"{API}/destinations/"
        self.assertEqual(self.client.get(url).data["count"], 3)
        self.assertEqual(self.client.get(url, {"continent": "EUROPE"}).data["count"], 1)
        self.assertEqual(self.client.get(url, {"country": "fr"}).data["count"], 1)
        response = self.client.get(url, {"country": "FRA"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data["error"]["details"]), {"country"})

    def test_detail_lists_only_published_offers_and_rating(self):
        destination = make_destination(attractions="Plage d'Assinie\n- Basilique\n\n")
        make_tour(destination=destination)
        make_tour(destination=destination, is_published=False)
        make_residence(destination=destination)
        make_activity(destination=destination)
        for rating, status in [(5, "APPROUVE"), (4, "APPROUVE"), (1, "EN_ATTENTE")]:
            Review.objects.create(
                destination=destination, rating=rating, status=status,
                author_name="Awa", author_email="awa@example.com", comment="Superbe",
            )

        data = self.client.get(f"{API}/destinations/{destination.slug}/").data
        self.assertEqual(data["attractions"], ["Plage d'Assinie", "Basilique"])
        self.assertEqual(len(data["tours"]), 1)
        self.assertEqual(len(data["residences"]), 1)
        self.assertEqual(set(data["residences"][0]), {
            "id", "slug", "name", "short_description", "rooms_count", "capacity",
            "cover_image", "cover_alt", "price_per_night",
        })
        self.assertEqual(len(data["activities"]), 1)
        self.assertEqual(data["rating"], {"average": 4.5, "count": 2})

    def test_unpublished_destination_is_404(self):
        hidden = make_destination(is_published=False)
        response = self.client.get(f"{API}/destinations/{hidden.slug}/")
        self.assertEqual(response.status_code, 404)
