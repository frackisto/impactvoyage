from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.core.formatting import format_amount
from apps.core.models import SiteSettings
from apps.core.tests.factories import UserFactory
from apps.notifications import tasks
from apps.notifications.emails import Email, frontend_url, pick, render, send_email
from apps.notifications.models import Notification
from apps.notifications.services import notify_staff


def sample(**kwargs):
    defaults = {"subject": "Sujet", "heading": "Titre", "greeting": "Bonjour Awa,",
                "paragraphs": ["Premier paragraphe.\nDeuxième ligne."],
                "details": [("Référence", "IV-2026-000001")],
                "action": ("Suivre ma réservation", "https://example.com/suivi?token=abc")}
    return Email(**{**defaults, **kwargs})


class RenderingTests(TestCase):
    def test_html_and_text_versions_carry_the_same_content(self):
        subject, text, html = render(sample())
        self.assertEqual(subject, "Sujet")
        self.assertIn('<html lang="fr">', html)
        self.assertIn("Premier paragraphe.<br>Deuxième ligne.", html)
        self.assertIn('href="https://example.com/suivi?token=abc"', html)
        self.assertIn("- Référence : IV-2026-000001", text)
        self.assertIn("Suivre ma réservation : https://example.com/suivi?token=abc", text)
        self.assertIn("L'équipe Impact Voyage", text)

    def test_customer_content_is_escaped_in_html(self):
        _, text, html = render(sample(paragraphs=["<script>alert(1)</script> & co"]))
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("<script>alert(1)</script> & co", text)  # texte brut : tel quel

    def test_layout_follows_the_language(self):
        _, text, html = render(sample(language="en"))
        self.assertIn('<html lang="en">', html)
        self.assertIn("The Impact Voyage team", text)
        self.assertIn("- Référence: IV-2026-000001", text)

    def test_footer_uses_the_agency_details(self):
        site = SiteSettings.load()
        site.phone, site.email = "+225 01 02 03 04 05", "bonjour@agence.example"
        site.save()
        _, text, html = render(sample())
        self.assertIn("+225 01 02 03 04 05", html)
        self.assertIn("bonjour@agence.example", text)

    def test_agency_emails_have_no_customer_signature(self):
        _, text, _ = render(sample(for_agency=True))
        self.assertNotIn("L'équipe Impact Voyage", text)
        self.assertIn("Notification automatique", text)

    def test_links_and_texts_in_the_customer_language(self):
        self.assertEqual(frontend_url("/devis", "fr"), "http://localhost:3000/devis")
        self.assertEqual(frontend_url("/devis", "en-GB"), "http://localhost:3000/en/devis")
        self.assertEqual(frontend_url("/devis", "de"), "http://localhost:3000/devis")
        self.assertEqual(pick("en", "Bonjour", "Hello"), "Hello")
        self.assertEqual(pick(None, "Bonjour", "Hello"), "Bonjour")
        self.assertEqual(format_amount(1250000, "XOF", "en"), "1,250,000 FCFA")
        self.assertEqual(format_amount(1250000), "1 250 000 FCFA")


class SendingTests(TestCase):
    def test_multipart_email_sent_after_commit_with_the_agency_as_reply_to(self):
        site = SiteSettings.load()
        site.email = "bonjour@agence.example"
        site.save()
        with self.captureOnCommitCallbacks(execute=True):
            send_email("awa@example.com", sample())
        message = mail.outbox[0]
        self.assertEqual(message.to, ["awa@example.com"])
        self.assertEqual(message.reply_to, ["bonjour@agence.example"])
        self.assertIn("Suivre ma réservation", message.body)
        html, mimetype = message.alternatives[0]
        self.assertEqual(mimetype, "text/html")
        self.assertIn("<h1", html)

    def test_nothing_is_sent_when_the_transaction_fails(self):
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            send_email("awa@example.com", sample())
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(mail.outbox, [])


class StaffChannelsTests(TestCase):
    def setUp(self):
        self.admin = UserFactory(role="ADMIN", whatsapp="+2250700000001", phone="+2250700000011")
        self.commercial = UserFactory(role="COMMERCIAL", whatsapp="+2250700000002")
        self.manager = UserFactory(role="GESTIONNAIRE", whatsapp="+2250700000003")

    def test_dashboard_and_agency_email_by_default(self):
        with self.captureOnCommitCallbacks(execute=True):
            notify_staff(Notification.Event.CONTACT_RECEIVED, "Message de Koffi", "Bonjour",
                         link="/admin/inquiries/contactmessage/1/change/",
                         details=[("Objet", "Visa")], reply_to=["koffi@example.com"])
        self.assertEqual(
            set(Notification.objects.values_list("recipient", flat=True)),
            {self.admin.pk, self.commercial.pk},  # pas le gestionnaire
        )
        message = mail.outbox[0]
        self.assertEqual(message.to, ["contact@agence-voyage.com"])
        self.assertEqual(message.reply_to, ["koffi@example.com"])  # répondre = écrire au client
        self.assertIn("http://localhost:8000/admin/inquiries/contactmessage/1/change/", message.body)
        self.assertIn("- Objet : Visa", message.body)

    @override_settings(STAFF_NOTIFICATION_CHANNELS=[
        "apps.notifications.channels.WhatsAppChannel", "apps.notifications.channels.SmsChannel",
    ])
    def test_whatsapp_and_sms_channels_are_ready(self):
        sent = []
        backend = mock.Mock(send=lambda channel, to, text: sent.append((channel, to, text)))
        with mock.patch("apps.notifications.channels.ConsoleBackend", return_value=backend), \
             self.captureOnCommitCallbacks(execute=True):
            notify_staff(Notification.Event.QUOTE_DECLINED, "Devis DV-1 refusé",
                         link="/admin/inquiries/quoterequest/1/change/")
        whatsapp = sorted(to for channel, to, _ in sent if channel == "whatsapp")
        self.assertEqual(whatsapp, ["+2250700000001", "+2250700000002"])
        self.assertEqual([to for channel, to, _ in sent if channel == "sms"], ["+2250700000011"])
        self.assertIn("Devis DV-1 refusé", sent[0][2])
        self.assertFalse(Notification.objects.exists())  # canal du tableau de bord retiré
        self.assertEqual(mail.outbox, [])


class PurgeTests(TestCase):
    def test_read_notifications_are_purged_after_the_retention_period(self):
        user = UserFactory(role="ADMIN")
        old = timezone.now() - timedelta(days=120)
        for is_read, read_at in [(True, old), (True, timezone.now()), (False, None)]:
            Notification.objects.create(recipient=user, event="CONTACT_RECEIVED", title="x",
                                        is_read=is_read, read_at=read_at)
        self.assertEqual(tasks.purge_read_notifications_task(), 1)
        self.assertEqual(Notification.objects.count(), 2)


class PreviewCommandTests(TestCase):
    def test_writes_every_email_in_both_languages(self):
        import tempfile
        from io import StringIO
        from pathlib import Path

        from django.core.management import call_command

        call_command("seed_demo", verbosity=0)
        with tempfile.TemporaryDirectory() as folder:
            call_command("preview_emails", out=folder, stdout=StringIO())
            names = sorted(p.name for p in Path(folder).glob("*.html"))
            self.assertIn("booking-confirmed.fr.html", names)
            self.assertIn("quote-proposal.en.html", names)
            self.assertEqual(len(names), 25)
        self.assertEqual(mail.outbox, [])  # rien n'est envoyé
