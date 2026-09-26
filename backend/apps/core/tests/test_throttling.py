from unittest import mock

from django.test import override_settings

from apps.core import throttling
from apps.core.tests.test_api import API, ApiTestCase

SECRET = "s" * 40
RATES = {"anon": "2/min", "user": "2/min", "auth": "2/min"}


@override_settings(FRONTEND_SHARED_SECRET=SECRET)
@mock.patch.object(throttling.AnonRateThrottle, "THROTTLE_RATES", RATES)
@mock.patch.object(throttling.ScopedRateThrottle, "THROTTLE_RATES", RATES)
class FrontendThrottlingTests(ApiTestCase):
    """Limites de débit quand les pages sont rendues par le serveur Next.js (architecture § 5)."""

    def get(self, **headers):
        return self.client.get(f"{API}/destinations/", **headers).status_code

    def login(self, **headers):
        return self.client.post(
            f"{API}/auth/login/", {"email": "x@example.com", "password": "faux"}, **headers
        ).status_code

    def test_cached_reads_from_the_frontend_are_not_limited(self):
        statuses = [self.get(HTTP_X_FRONTEND_SECRET=SECRET) for _ in range(4)]
        self.assertEqual(statuses, [200] * 4)

    def test_limit_applies_to_each_visitor_forwarded_by_the_frontend(self):
        visitor = {"HTTP_X_FRONTEND_SECRET": SECRET, "HTTP_X_CLIENT_IP": "203.0.113.7"}
        self.assertEqual([self.get(**visitor) for _ in range(3)], [200, 200, 429])
        # Un autre visiteur n'est pas pénalisé.
        other = {**visitor, "HTTP_X_CLIENT_IP": "203.0.113.8"}
        self.assertEqual(self.get(**other), 200)

    def test_writes_stay_limited_even_without_client_ip(self):
        statuses = [self.login(HTTP_X_FRONTEND_SECRET=SECRET) for _ in range(3)]
        self.assertEqual(statuses[-1], 429)

    def test_forged_headers_do_not_bypass_limits(self):
        # Sans le bon secret, X-Client-IP est ignoré ; X-Forwarded-For aussi (NUM_PROXIES = 0).
        forged = [
            self.get(HTTP_X_FRONTEND_SECRET="faux", HTTP_X_CLIENT_IP=f"198.51.100.{n}",
                     HTTP_X_FORWARDED_FOR=f"198.51.100.{n}")
            for n in range(3)
        ]
        self.assertEqual(forged, [200, 200, 429])

    def test_invalid_client_ip_falls_back_to_remote_address(self):
        headers = {"HTTP_X_FRONTEND_SECRET": SECRET, "HTTP_X_CLIENT_IP": "pas-une-ip"}
        # Adresse invalide : lecture traitée comme une lecture du serveur (non limitée).
        self.assertEqual([self.get(**headers) for _ in range(3)], [200, 200, 200])
