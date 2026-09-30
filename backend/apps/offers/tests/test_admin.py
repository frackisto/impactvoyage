from django.urls import reverse

from apps.core.tests.admin_helpers import AdminTestCase, change_form_data
from apps.core.tests.factories import OfferFactory, TourFactory, VehicleFactory, in_days
from apps.offers.models import Offer


class OfferAdminTests(AdminTestCase):
    def setUp(self):
        self.login("GESTIONNAIRE")  # rôle chargé des offres
        self.offer = OfferFactory()
        self.url = reverse("admin:offers_offer_change", args=[self.offer.pk])

    def submit(self, **changes):
        return self.client.post(self.url, change_form_data(self.client.get(self.url), _save="", **changes))

    def errors(self, response):
        form = response.context["adminform"].form
        return {field: " ".join(messages) for field, messages in form.errors.items()}

    def test_readable_errors_instead_of_database_constraints(self):
        errors = self.errors(self.submit(promo_price="250000"))
        self.assertIn("inférieur au prix initial", errors["promo_price"])

        errors = self.errors(self.submit(start_date=in_days(5), end_date=in_days(2)))
        self.assertIn("doit suivre son début", errors["end_date"])

        errors = self.errors(self.submit(tour=TourFactory().pk, vehicle=VehicleFactory().pk))
        self.assertIn("au plus une fiche", errors["__all__"])

    def test_valid_change_is_saved(self):
        tour = TourFactory()
        self.assertEqual(self.submit(tour=tour.pk, title_fr="Promo d'été").status_code, 302)
        self.offer.refresh_from_db()
        self.assertEqual((self.offer.tour, self.offer.title_fr), (tour, "Promo d'été"))

    def test_bulk_activation(self):
        changelist = reverse("admin:offers_offer_changelist")
        self.client.post(changelist, {"action": "deactivate", "_selected_action": [self.offer.pk]})
        self.assertFalse(Offer.objects.currently_active().exists())
        self.client.post(changelist, {"action": "activate", "_selected_action": [self.offer.pk]})
        self.assertTrue(Offer.objects.currently_active().exists())
