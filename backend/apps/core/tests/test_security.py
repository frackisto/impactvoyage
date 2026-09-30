"""Sécurité (Phase 23) : en-têtes, documentation, anti-spam, contrôles des images."""
import json
from io import BytesIO
from unittest import mock
from urllib.error import URLError

from django.core.checks import run_checks
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.accounts.models import User
from apps.core import validators
from apps.core.captcha import verify_captcha
from apps.inquiries.models import ContactMessage
from apps.notifications.services import admin_path
from apps.reviews.models import Review

from .factories import ContactMessageFactory, TourFactory, UserFactory
from .test_api import API, ApiTestCase


def image_file(name="photo.jpg", fmt="JPEG", size=(40, 30), exif=None):
    buffer = BytesIO()
    options = {"exif": exif} if exif is not None else {}
    Image.new("RGB", size, "teal").save(buffer, format=fmt, **options)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


def cloudflare(result):
    """Réponse simulée de l'API siteverify de Turnstile."""
    response = mock.MagicMock()
    response.__enter__.return_value = BytesIO(json.dumps(result).encode())
    return mock.patch("apps.core.captcha.urlopen", return_value=response)


class SecurityHeadersTests(TestCase):
    def test_api_responses_forbid_any_resource_and_framing(self):
        response = self.client.get(f"{API}/health/")
        self.assertEqual(response["Content-Security-Policy"],
                         "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; "
                         "form-action 'none'")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_admin_only_loads_its_own_resources(self):
        response = self.client.get(reverse("admin:login"))
        csp = response["Content-Security-Policy"]
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertNotIn("https:", csp)

    def test_api_docs_keep_their_cdn_scripts(self):
        response = self.client.get(reverse("swagger-ui"))
        self.assertNotIn("Content-Security-Policy", response)


@override_settings(API_DOCS_PUBLIC=False)
class ApiDocsAccessTests(TestCase):
    def test_docs_are_reserved_to_verified_staff(self):
        for name in ("schema", "swagger-ui", "redoc"):
            with self.subTest(name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 403)

        self.client.force_login(UserFactory())
        self.assertEqual(self.client.get(reverse("schema")).status_code, 403)

        self.client.force_login(UserFactory(role=User.Role.AGENT))
        self.assertEqual(self.client.get(reverse("schema")).status_code, 200)
        with override_settings(STAFF_OTP_REQUIRED=True):  # session non vérifiée par un code
            self.assertEqual(self.client.get(reverse("schema")).status_code, 403)


@override_settings(TURNSTILE_SECRET_KEY="secret-de-test")
class CaptchaTests(ApiTestCase):
    CONTACT = {"name": "Koffi", "email": "koffi@example.com", "subject": "Visa",
               "message": "Bonjour, je voudrais un visa pour le Canada."}

    def test_valid_token_is_checked_with_the_visitor_address(self):
        with cloudflare({"success": True}) as urlopen:
            response = self.client.post(f"{API}/contact/", {**self.CONTACT, "captcha_token": "ok"},
                                        REMOTE_ADDR="203.0.113.9")
        self.assertEqual(response.status_code, 201)
        body = urlopen.call_args.args[0].data.decode()
        self.assertIn("response=ok", body)
        self.assertIn("remoteip=203.0.113.9", body)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_missing_or_refused_token_blocks_the_form(self):
        with cloudflare({"success": False, "error-codes": ["invalid-input-response"]}):
            refused = self.client.post(f"{API}/contact/", {**self.CONTACT, "captcha_token": "x"})
        missing = self.client.post(f"{API}/contact/", self.CONTACT)
        for response in (refused, missing):
            self.assertEqual(response.status_code, 400)
            self.assertIn("anti-robot", response.data["error"]["details"]["non_field_errors"][0])
        self.assertFalse(ContactMessage.objects.exists())

    def test_token_is_not_spent_on_invalid_data(self):
        with cloudflare({"success": True}) as urlopen:
            response = self.client.post(f"{API}/contact/", {**self.CONTACT, "message": "court",
                                                             "captcha_token": "ok"})
        self.assertEqual(response.status_code, 400)
        urlopen.assert_not_called()

    def test_cloudflare_outage_does_not_lose_requests(self):
        with mock.patch("apps.core.captcha.urlopen", side_effect=URLError("timeout")):
            self.assertTrue(verify_captcha("jeton"))

    def test_quote_and_review_forms_are_protected_too(self):
        tour = TourFactory()
        quote = {"first_name": "Awa", "last_name": "Koné", "email": "awa@example.com",
                 "phone": "+2250700000000", "consent": True}
        review = {"author_name": "Awa", "author_email": "awa@example.com", "rating": 5,
                  "comment": "Un voyage magnifique.", "target_type": "tour",
                  "target_slug": tour.slug}
        for path, data in (("quotes", quote), ("reviews", review)):
            with self.subTest(path):
                self.assertEqual(self.client.post(f"{API}/{path}/", data).status_code, 400)

    @override_settings(TURNSTILE_SECRET_KEY="")
    def test_verification_is_disabled_without_secret(self):
        self.assertTrue(verify_captcha(""))


class ImageUploadTests(ApiTestCase):
    def test_real_format_must_match_the_extension(self):
        validators.validate_image_content(image_file())
        with self.assertRaises(ValidationError) as ctx:
            validators.validate_image_content(image_file(name="photo.jpg", fmt="GIF"))
        self.assertEqual(ctx.exception.code, "image_format_mismatch")
        with self.assertRaises(ValidationError) as ctx:
            validators.validate_image_content(
                SimpleUploadedFile("photo.png", b"<svg onload=alert(1)>"))
        self.assertEqual(ctx.exception.code, "invalid_image")

    def test_oversized_images_are_refused_before_decoding(self):
        with mock.patch.object(validators, "MAX_IMAGE_PIXELS", 100), \
                self.assertRaises(ValidationError) as ctx:
            validators.validate_image_content(image_file(size=(20, 10)))
        self.assertEqual(ctx.exception.code, "image_too_large")

    def test_review_photo_loses_its_gps_metadata(self):
        exif = Image.Exif()
        exif[0x010F] = "Téléphone"  # fabricant
        exif[0x8825] = {1: "N", 2: (5.0, 20.0, 0.0)}  # position GPS
        tour = TourFactory()
        response = self.client.post(f"{API}/reviews/", {
            "author_name": "Awa", "author_email": "awa@example.com", "rating": 5,
            "comment": "Un voyage magnifique.", "target_type": "tour", "target_slug": tour.slug,
            "photo": image_file(exif=exif),
        }, format="multipart")
        self.assertEqual(response.status_code, 201)
        review = Review.objects.get()
        with Image.open(review.photo) as stored:
            self.assertEqual(stored.format, "JPEG")
            self.assertEqual(dict(stored.getexif()), {})

    def test_review_photo_with_a_lying_extension_is_refused(self):
        tour = TourFactory()
        response = self.client.post(f"{API}/reviews/", {
            "author_name": "Awa", "author_email": "awa@example.com", "rating": 5,
            "comment": "Un voyage magnifique.", "target_type": "tour", "target_slug": tour.slug,
            "photo": image_file(name="photo.jpg", fmt="PNG"),
        }, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("photo", response.data["error"]["details"])
        self.assertFalse(Review.objects.exists())


class AdminLinksTests(TestCase):
    def test_reply_link_cannot_inject_recipients(self):
        message = ContactMessageFactory(subject="Visa&bcc=pirate@example.com\nCc: x")
        admin = UserFactory(role=User.Role.SUPER_ADMIN)
        self.client.force_login(admin)
        page = self.client.get(reverse("admin:inquiries_contactmessage_change",
                                       args=[message.pk]))
        self.assertContains(page, "subject=Re%3A%20Visa%26bcc%3Dpirate%40example.com%0ACc%3A%20x")
        self.assertNotContains(page, "&bcc=pirate")

    @override_settings(ROOT_URLCONF="apps.core.tests.urls_custom_admin")
    def test_notification_links_follow_the_admin_address(self):
        message = ContactMessageFactory()
        self.assertEqual(admin_path(message),
                         f"/gestion-x7/inquiries/contactmessage/{message.pk}/change/")


class DeployChecksTests(TestCase):
    def ids(self):
        return {issue.id for issue in run_checks(include_deployment_checks=True)}

    @override_settings(TURNSTILE_SECRET_KEY="", ADMIN_URL="admin/", STAFF_OTP_REQUIRED=False)
    def test_missing_protections_are_reported(self):
        self.assertTrue({"core.W002", "core.W003", "core.W004"} <= self.ids())

    @override_settings(TURNSTILE_SECRET_KEY="clé", ADMIN_URL="gestion-x7/", STAFF_OTP_REQUIRED=True)
    def test_complete_configuration_is_silent(self):
        self.assertFalse({"core.W002", "core.W003", "core.W004"} & self.ids())
