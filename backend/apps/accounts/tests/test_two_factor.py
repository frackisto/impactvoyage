"""Double authentification de l'équipe et protection du backoffice (Phase 23)."""
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django_otp.oath import totp
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.accounts import otp
from apps.accounts.models import User
from apps.core.tests.factories import PASSWORD, UserFactory
from apps.core.tests.test_api import API, ApiTestCase


def code_for(device):
    """Code TOTP courant ; dernier code utilisé et délai d'échec oubliés (tests successifs)."""
    device.refresh_from_db()
    device.last_t = -1
    device.throttling_failure_count = 0
    device.save(update_fields=["last_t", "throttling_failure_count"])
    return f"{totp(device.bin_key, device.step, device.t0, device.digits, device.drift):06d}"


def enroll(user):
    """Application enregistrée et confirmée ; renvoie (appareil, codes de secours)."""
    device = otp.pending_totp_device(user)
    codes = otp.confirm_totp_device(device, code_for(device))
    device.refresh_from_db()
    return device, codes


@override_settings(STAFF_OTP_REQUIRED=True)
class AdminTwoFactorTests(TestCase):
    def setUp(self):
        cache.clear()
        self.agent = UserFactory(role=User.Role.ADMIN)
        self.client.force_login(self.agent)
        self.index = reverse("admin:index")

    def test_first_access_requires_enrolling_an_authenticator(self):
        response = self.client.get(self.index)
        self.assertRedirects(response, f"{reverse('admin-2fa-setup')}?next=%2Fadmin%2F",
                             fetch_redirect_response=False)

        page = self.client.get(reverse("admin-2fa-setup"))
        self.assertContains(page, "<svg")  # QR code
        device = TOTPDevice.objects.get(user=self.agent, confirmed=False)

        wrong = self.client.post(reverse("admin-2fa-setup"), {"code": "000000"})
        self.assertContains(wrong, "Code incorrect")
        self.assertFalse(otp.has_confirmed_device(self.agent))

        done = self.client.post(reverse("admin-2fa-setup"),
                                {"code": code_for(device), "next": self.index})
        self.assertEqual(len(done.context["codes"]), 10)
        self.assertContains(done, done.context["codes"][0])
        self.assertEqual(self.client.get(self.index).status_code, 200)

    def test_each_login_asks_for_a_code_and_accepts_a_backup_code_once(self):
        device, codes = enroll(self.agent)
        response = self.client.get(self.index)
        self.assertRedirects(response, f"{reverse('admin-2fa-verify')}?next=%2Fadmin%2F",
                             fetch_redirect_response=False)
        # Sans code valide, impossible d'enregistrer une autre application.
        self.assertRedirects(self.client.get(reverse("admin-2fa-setup")),
                             reverse("admin-2fa-verify"), fetch_redirect_response=False)

        wrong = self.client.post(reverse("admin-2fa-verify"), {"code": "123456"})
        self.assertContains(wrong, "Code incorrect")
        session_key = self.client.session.session_key
        ok = self.client.post(reverse("admin-2fa-verify"),
                              {"code": codes[0].upper(), "next": self.index})
        self.assertRedirects(ok, self.index, fetch_redirect_response=False)
        self.assertNotEqual(self.client.session.session_key, session_key)  # clé renouvelée
        self.assertEqual(self.client.get(self.index).status_code, 200)

        # Nouvelle session : le code de secours déjà utilisé ne sert plus.
        self.client.logout()
        self.client.force_login(self.agent)
        again = self.client.post(reverse("admin-2fa-verify"), {"code": codes[0]})
        self.assertEqual(again.status_code, 200)
        StaticDevice.objects.update(throttling_failure_count=0)
        with self.subTest("application"):
            ok = self.client.post(reverse("admin-2fa-verify"), {"code": code_for(device)})
            self.assertEqual(ok.status_code, 302)

    def test_next_parameter_cannot_redirect_to_another_site(self):
        device, _ = enroll(self.agent)
        response = self.client.post(reverse("admin-2fa-verify"),
                                    {"code": code_for(device), "next": "https://evil.example/"})
        self.assertRedirects(response, self.index, fetch_redirect_response=False)

    def test_clients_and_anonymous_visitors_cannot_use_the_pages(self):
        self.client.logout()
        response = self.client.get(reverse("admin-2fa-verify"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    @override_settings(STAFF_OTP_REQUIRED=False)
    def test_disabled_two_factor_lets_staff_in(self):
        self.assertEqual(self.client.get(self.index).status_code, 200)

    def test_superadmin_can_reset_a_lost_authenticator(self):
        enroll(self.agent)
        boss = UserFactory(role=User.Role.SUPER_ADMIN)
        boss_device, _ = enroll(boss)
        self.client.force_login(boss)
        self.client.post(reverse("admin-2fa-verify"), {"code": code_for(boss_device)})

        url = reverse("admin:accounts_user_reset_two_factor", args=[self.agent.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(url, {})
        self.assertFalse(otp.has_confirmed_device(self.agent))
        self.assertFalse(StaticDevice.objects.filter(user=self.agent).exists())

        listing = self.client.get(reverse("admin:accounts_user_changelist"))
        self.assertContains(listing, "À configurer")

    def test_admin_cannot_reset_two_factor(self):
        device, _ = enroll(self.agent)
        self.client.post(reverse("admin-2fa-verify"), {"code": code_for(device)})
        other = UserFactory(role=User.Role.AGENT)
        enroll(other)
        url = reverse("admin:accounts_user_reset_two_factor", args=[other.pk])
        self.client.post(url, {})
        self.assertTrue(otp.has_confirmed_device(other))


class AdminLoginThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = UserFactory(role=User.Role.AGENT, email="agent@example.com")
        self.url = reverse("admin:login")

    def attempt(self, password="mauvais", email="agent@example.com"):
        return self.client.post(self.url, {"username": email, "password": password})

    @override_settings(ADMIN_LOGIN_MAX_FAILURES=3)
    def test_account_is_locked_after_repeated_failures(self):
        for _ in range(3):
            self.assertEqual(self.attempt().status_code, 200)
        locked = self.attempt(password=PASSWORD)
        self.assertEqual(locked.status_code, 429)
        self.assertContains(locked, "Trop de tentatives", status_code=429)

    @override_settings(ADMIN_LOGIN_MAX_FAILURES=3)
    def test_success_resets_the_counter(self):
        self.attempt()
        self.attempt()
        self.assertEqual(self.attempt(password=PASSWORD).status_code, 302)
        self.client.logout()
        for _ in range(2):
            self.attempt()
        self.assertEqual(self.attempt(password=PASSWORD).status_code, 302)


@override_settings(STAFF_OTP_REQUIRED=True)
class ApiLoginTwoFactorTests(ApiTestCase):
    def login(self, email, **extra):
        return self.client.post(f"{API}/auth/login/",
                                {"email": email, "password": PASSWORD, **extra})

    def test_staff_login_requires_a_code(self):
        agent = UserFactory(role=User.Role.COMMERCIAL, email="commercial@example.com")
        response = self.login(agent.email)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"]["code"], "otp_setup_required")

        device, _ = enroll(agent)
        self.assertEqual(self.login(agent.email).data["error"]["code"], "otp_required")
        self.assertEqual(self.login(agent.email, otp_code="000000").data["error"]["code"],
                         "otp_invalid")
        ok = self.login(agent.email, otp_code=code_for(device))
        self.assertEqual(ok.status_code, 200)
        self.assertIn("access", ok.data)

    def test_clients_log_in_with_a_password_only(self):
        client = UserFactory(email="client@example.com")
        self.assertEqual(self.login(client.email).status_code, 200)

    def test_wrong_password_is_refused_before_asking_for_a_code(self):
        UserFactory(role=User.Role.AGENT, email="agent@example.com")
        response = self.client.post(f"{API}/auth/login/",
                                    {"email": "agent@example.com", "password": "faux"})
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("otp", response.data["error"]["code"])
