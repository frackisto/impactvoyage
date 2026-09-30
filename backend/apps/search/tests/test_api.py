from decimal import Decimal

from apps.core.tests.factories import (
    ActivityFactory,
    DestinationFactory,
    TourFactory,
    VehicleFactory,
)
from apps.core.tests.test_api import API, ApiTestCase


class GlobalSearchTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.dubai = DestinationFactory(name_fr="Dubaï", name_en="Dubai", slug="dubai", country_code="AE")
        self.tour = TourFactory(title_fr="Dubaï, la ville des records", destination=self.dubai,
                              base_price=Decimal("850000"))
        self.safari = ActivityFactory(title_fr="Safari dans le désert", destination=self.dubai)
        self.bassam = DestinationFactory(name_fr="Grand-Bassam", slug="grand-bassam")
        TourFactory(title_fr="Escapade balnéaire", destination=self.bassam)
        TourFactory(title_fr="Dubaï secret", destination=self.dubai, is_published=False)

    def search(self, **params):
        response = self.client.get(f"{API}/search/", params)
        self.assertEqual(response.status_code, 200)
        return response.data

    def test_tolerates_typos_and_accents_across_types(self):
        for query in ("Dubaï", "dubai", "dubay"):
            data = self.search(q=query)
            self.assertEqual(data["counts"]["destination"], 1, query)
            self.assertEqual(data["counts"]["tour"], 1, query)  # le circuit non publié est exclu
            self.assertEqual(data["counts"]["activity"], 1, query)  # via sa destination
            self.assertEqual(data["results"][0]["slug"], "dubai", query)

    def test_every_word_must_match(self):
        data = self.search(q="safari dubai")
        self.assertEqual([r["slug"] for r in data["results"]], [self.safari.slug])
        self.assertEqual(self.search(q="chien")["count"], 0)
        self.assertEqual(self.search(q="de la")["count"], 0)  # mots vides seulement

    def test_result_shape_and_price(self):
        tour = next(r for r in self.search(q="records")["results"] if r["type"] == "tour")
        self.assertEqual(tour["title"], "Dubaï, la ville des records")
        self.assertEqual(tour["context"], "Dubaï")
        self.assertEqual(tour["price"]["amount"], "850000.00")
        self.assertEqual(tour["price_unit"], "person")

    def test_type_and_destination_filters(self):
        data = self.search(q="dubai", type="tour,activity")
        self.assertEqual(set(data["counts"]), {"tour", "activity"})
        VehicleFactory(brand="Toyota", model="Dubai Edition")
        # Un véhicule n'a pas de destination : exclu quand une destination est imposée.
        self.assertNotIn("vehicle", self.search(q="dubai", destination="dubai")["counts"])
        self.assertEqual(self.search(q="escapade", destination="dubai")["count"], 0)

    def test_invalid_parameters(self):
        self.assertEqual(self.client.get(f"{API}/search/").status_code, 400)
        response = self.client.get(f"{API}/search/", {"q": "dubai", "type": "planete"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("type", response.data["error"]["details"])
