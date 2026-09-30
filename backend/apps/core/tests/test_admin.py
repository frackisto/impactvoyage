from decimal import Decimal
from unittest import mock

from django.contrib import admin
from django.core.cache import cache
from django.core.management import call_command
from django.urls import reverse

from apps.core.models import ExchangeRate, SiteSettings
from apps.core.services import RATES_CACHE_KEY, get_rates
from apps.tours.models import Tour

from .admin_helpers import AdminTestCase, change_form_data


class BackofficeSmokeTests(AdminTestCase):
    """Chaque écran de l'admin s'affiche, avec les données de démonstration."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def test_every_registered_screen_renders_for_the_super_admin(self):
        self.login("SUPER_ADMIN")
        for model in admin.site._registry:
            opts = model._meta
            with self.subTest(model=opts.label):
                changelist = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
                response = self.client.get(changelist, follow=True)
                self.assertEqual(response.status_code, 200)

                add = self.client.get(reverse(f"admin:{opts.app_label}_{opts.model_name}_add"))
                self.assertIn(add.status_code, (200, 403))

                obj = model._default_manager.first()
                if obj is not None:
                    change = reverse(f"admin:{opts.app_label}_{opts.model_name}_change",
                                     args=[obj.pk])
                    self.assertEqual(self.client.get(change).status_code, 200)

    def test_search_and_filters_work_on_main_lists(self):
        self.login("SUPER_ADMIN")
        for url in (
            reverse("admin:tours_tour_changelist") + "?q=dubai&scope__exact=INTERNATIONAL",
            reverse("admin:bookings_booking_changelist") + "?status__in=REQUESTED,PENDING",
            reverse("admin:inquiries_quoterequest_changelist") + "?q=DV-DEMO",
            reverse("admin:accommodations_hotel_changelist") + "?q=lagune",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_translated_content_shows_one_field_per_language(self):
        self.login("AGENT")
        tour = Tour.objects.get(slug="dubai-ville-des-records")
        response = self.client.get(reverse("admin:tours_tour_change", args=[tour.pk]))
        fields = response.context["adminform"].form.fields
        self.assertIn("title_fr", fields)
        self.assertIn("title_en", fields)
        self.assertNotIn("title", fields)

    def test_editing_a_tour_keeps_departures_and_program(self):
        self.login("AGENT")
        tour = Tour.objects.get(slug="dubai-ville-des-records")
        url = reverse("admin:tours_tour_change", args=[tour.pk])
        data = change_form_data(self.client.get(url), title_en="Dubai, city of records", _save="")
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("admin:tours_tour_changelist"))
        tour.refresh_from_db()
        self.assertEqual(tour.title_en, "Dubai, city of records")
        self.assertEqual(tour.departures.count(), 3)
        self.assertEqual(tour.days.count(), 6)


class LoginTests(AdminTestCase):
    def test_login_page_opened_directly_leads_to_the_dashboard(self):
        from apps.core.tests.factories import UserFactory

        UserFactory(role="COMMERCIAL", email="equipe@example.com")
        response = self.client.post(reverse("admin:login"), {
            "username": "equipe@example.com", "password": "mot-de-passe",
        })
        self.assertRedirects(response, reverse("admin:index"))


class SiteSettingsAdminTests(AdminTestCase):
    def test_list_opens_the_single_settings_page(self):
        self.login("SUPER_ADMIN")
        response = self.client.get(reverse("admin:core_sitesettings_changelist"))
        self.assertRedirects(response, reverse("admin:core_sitesettings_change", args=[1]))
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_admin_role_can_read_but_not_change_settings(self):
        self.login("ADMIN")
        url = reverse("admin:core_sitesettings_change", args=[SiteSettings.load().pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_change_permission"])
        self.assertEqual(self.client.post(url, {"agency_name": "Autre"}).status_code, 403)


class ExchangeRateAdminTests(AdminTestCase):
    def setUp(self):
        cache.clear()

    def test_refresh_asks_for_confirmation_then_updates_rates(self):
        self.login("SUPER_ADMIN")
        url = reverse("admin:core_exchangerate_refresh_rates")
        fetch = mock.Mock(return_value={"USD": Decimal("1.1"), "GBP": Decimal("0.85")})
        with mock.patch("apps.core.services.fetch_eur_rates", fetch):
            response = self.client.get(url)
            self.assertTemplateUsed(response, "admin/decision_form.html")
            self.assertFalse(ExchangeRate.objects.exists())  # rien sans confirmation

            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(url)
        self.assertRedirects(response, reverse("admin:core_exchangerate_changelist"))
        self.assertEqual(ExchangeRate.objects.count(), 3)

    def test_editing_a_rate_refreshes_the_cached_rates(self):
        self.login("SUPER_ADMIN")
        rate = ExchangeRate.objects.create(currency="EUR", rate_from_xof=Decimal("0.0015"))
        self.assertEqual(get_rates()["EUR"], Decimal("0.0015"))
        url = reverse("admin:core_exchangerate_change", args=[rate.pk])
        data = change_form_data(self.client.get(url), rate_from_xof="0.0016", _save="")
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(url, data)
        self.assertIsNone(cache.get(RATES_CACHE_KEY))
        self.assertEqual(get_rates()["EUR"], Decimal("0.0016"))
