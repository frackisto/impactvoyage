import re
from datetime import timedelta

from django.core import mail
from django.test import override_settings
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.services import make_email_verification_token
from apps.core.tests.helpers import make_user
from apps.core.tests.test_api import API, ApiTestCase

PASSWORD = "Voyage-Assinie-2027"


class RegistrationTests(ApiTestCase):
    DATA = {"email": "Awa.Kone@Example.com", "password": PASSWORD, "first_name": "Awa",
            "last_name": "Koné", "consent": True}

    def test_register_returns_tokens_and_sends_verification_link(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(f"{API}/auth/register/", self.DATA)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"]["email"], "awa.kone@example.com")
        self.assertEqual(response.data["user"]["role"], "CLIENT")
        self.assertFalse(response.data["user"]["is_verified"])
        self.assertEqual(AccessToken(response.data["access"])["role"], "CLIENT")

        token = re.search(r"token=(\S+)", mail.outbox[0].body).group(1)
        self.assertEqual(self.client.post(f"{API}/auth/verify-email/", {"token": token})
                         .status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertTrue(self.client.get(f"{API}/auth/me/").data["is_verified"])

    def test_tampered_or_outdated_verification_token_is_refused(self):
        user = make_user()
        token = make_email_verification_token(user)
        bad = self.client.post(f"{API}/auth/verify-email/", {"token": token + "x"})
        self.assertEqual(bad.data["error"]["code"], "invalid_token")
        user.email = "nouvelle@example.com"
        user.save()
        self.assertEqual(self.client.post(f"{API}/auth/verify-email/", {"token": token})
                         .status_code, 400)
        with override_settings(EMAIL_VERIFICATION_MAX_AGE=-1):
            fresh = make_email_verification_token(user)
            self.assertEqual(self.client.post(f"{API}/auth/verify-email/", {"token": fresh})
                             .status_code, 400)


class LoginTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user("COMMERCIAL", email="commercial@example.com",
                              first_name="Yao", last_name="Kouamé")
        self.user.set_password(PASSWORD)
        self.user.save()

    def login(self, email="Commercial@Example.com", password=PASSWORD):
        return self.client.post(f"{API}/auth/login/", {"email": email, "password": password})

    def test_login_returns_tokens_with_role_and_profile(self):
        response = self.login(email="commercial@example.com")
        self.assertEqual(response.status_code, 200)
        claims = AccessToken(response.data["access"])
        self.assertEqual((claims["role"], claims["name"]), ("COMMERCIAL", "Yao Kouamé"))
        self.assertEqual(response.data["user"]["role_label"], "Commercial")
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_wrong_password_uses_the_error_format(self):
        response = self.login(email="commercial@example.com", password="faux")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"]["code"], "no_active_account")

    def test_refresh_rotation_and_logout(self):
        refresh = self.login(email="commercial@example.com").data["refresh"]
        rotated = self.client.post(f"{API}/auth/refresh/", {"refresh": refresh})
        self.assertEqual(rotated.status_code, 200)
        # L'ancien refresh token est révoqué par la rotation.
        self.assertEqual(self.client.post(f"{API}/auth/refresh/", {"refresh": refresh})
                         .status_code, 401)
        new_refresh = rotated.data["refresh"]
        self.assertEqual(self.client.post(f"{API}/auth/logout/", {"refresh": new_refresh})
                         .status_code, 200)
        self.assertEqual(self.client.post(f"{API}/auth/refresh/", {"refresh": new_refresh})
                         .status_code, 401)

    def test_login_is_rate_limited(self):
        for _ in range(10):
            self.login(email="commercial@example.com", password="faux")
        self.assertEqual(self.login(email="commercial@example.com").status_code, 429)


class ProfileAndPasswordTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(email="client@example.com")
        self.user.set_password(PASSWORD)
        self.user.save()
        tokens = self.client.post(f"{API}/auth/login/",
                                  {"email": "client@example.com", "password": PASSWORD}).data
        self.refresh = tokens["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def test_profile_update_cannot_change_role_or_email(self):
        response = self.client.patch(f"{API}/auth/me/", {
            "first_name": "Awa", "preferred_language": "en", "role": "SUPER_ADMIN",
            "email": "pirate@example.com",
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual((self.user.first_name, self.user.preferred_language), ("Awa", "en"))
        self.assertEqual((self.user.role, self.user.email), ("CLIENT", "client@example.com"))
        self.assertEqual(self.client.put(f"{API}/auth/me/", {}).status_code, 405)

    def test_password_change_revokes_refresh_tokens(self):
        wrong = self.client.post(f"{API}/auth/password/change/", {
            "current_password": "faux", "new_password": "Nouveau-Mot-De-Passe-42"})
        self.assertEqual(wrong.status_code, 400)
        ok = self.client.post(f"{API}/auth/password/change/", {
            "current_password": PASSWORD, "new_password": "Nouveau-Mot-De-Passe-42"})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(self.client.post(f"{API}/auth/refresh/", {"refresh": self.refresh})
                         .status_code, 401)

    def test_password_reset_flow_without_account_enumeration(self):
        self.client.credentials()
        with self.captureOnCommitCallbacks(execute=True):
            unknown = self.client.post(f"{API}/auth/password-reset/", {"email": "x@example.com"})
            known = self.client.post(f"{API}/auth/password-reset/", {"email": "client@example.com"})
        self.assertEqual(unknown.data, known.data)
        self.assertEqual(len(mail.outbox), 1)

        uid, token = re.search(r"uid=(\S+)&token=(\S+)", mail.outbox[0].body).groups()
        weak = self.client.post(f"{API}/auth/password-reset/confirm/",
                                {"uid": uid, "token": token, "new_password": "123"})
        self.assertIn("new_password", weak.data["error"]["details"])
        done = self.client.post(f"{API}/auth/password-reset/confirm/",
                                {"uid": uid, "token": token, "new_password": "Autre-Secret-2028"})
        self.assertEqual(done.status_code, 200)
        # Lien à usage unique.
        again = self.client.post(f"{API}/auth/password-reset/confirm/",
                                 {"uid": uid, "token": token, "new_password": "Encore-Autre-2029"})
        self.assertEqual(again.data["error"]["code"], "invalid_token")
        self.assertEqual(self.client.post(f"{API}/auth/refresh/", {"refresh": self.refresh})
                         .status_code, 401)

    def test_expired_access_token_is_refused(self):
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(seconds=1))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(f"{API}/auth/me/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"]["code"], "token_not_valid")
