from datetime import timedelta

from django.core import mail
from django.urls import reverse
from django.utils import timezone

from apps.core.tests.admin_helpers import AdminTestCase, change_form_data
from apps.core.tests.helpers import make_user
from apps.inquiries.models import ContactMessage, QuoteRequest

QStatus = QuoteRequest.Status


def make_quote(**kwargs):
    defaults = {"first_name": "Awa", "last_name": "Koné", "email": "awa@example.com",
                "phone": "+2250700000000", "destination_text": "Dubaï",
                "consent_at": timezone.now()}
    return QuoteRequest.objects.create(**{**defaults, **kwargs})


class QuoteAdminTests(AdminTestCase):
    def setUp(self):
        self.quote = make_quote()

    def url(self, name, quote=None):
        return reverse(f"admin:inquiries_quoterequest_{name}", args=[(quote or self.quote).pk])

    def test_sending_the_proposal_emails_the_client_link(self):
        commercial = self.login("COMMERCIAL")
        form_page = self.client.get(self.url("send_proposal_detail"))
        self.assertContains(form_page, "Envoyer la proposition")
        self.assertContains(form_page, "Dubaï")  # rappel de la demande

        valid_until = timezone.localdate() + timedelta(days=10)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.url("send_proposal_detail"), {
                "amount": "1250000", "valid_until": valid_until.isoformat(),
                "message": "Vols, hôtel 4 étoiles et safari compris.",
            })
        self.assertRedirects(response, self.url("change"))
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, QStatus.DEVIS_ENVOYE)
        self.assertEqual(self.quote.assigned_to, commercial)
        self.assertIn(f"token={self.quote.access_token}", mail.outbox[-1].body)

    def test_a_proposal_cannot_expire_in_the_past(self):
        self.login("COMMERCIAL")
        response = self.client.post(self.url("send_proposal_detail"), {
            "amount": "1000", "message": "…",
            "valid_until": (timezone.localdate() - timedelta(days=1)).isoformat(),
        })
        self.assertContains(response, "La date de validité est déjà passée.")
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, QStatus.NOUVELLE)

    def test_assigning_a_commercial_puts_the_quote_in_progress(self):
        self.login("COMMERCIAL")
        colleague = make_user("COMMERCIAL")
        response = self.client.get(self.url("change"))
        self.assertEqual(list(response.context["adminform"].form.fields), ["assigned_to"])
        self.client.post(self.url("change"), change_form_data(
            response, assigned_to=colleague.pk, _save=""))
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.assigned_to, colleague)
        self.assertEqual(self.quote.status, QStatus.EN_COURS)

    def test_refuse_button_on_the_quote_page(self):
        self.login("COMMERCIAL")
        response = self.client.get(self.url("change"))
        buttons = [a.action_name for a in response.context["actions_submit_line"]]
        self.assertIn("inquiries_quoterequest_refuse_submit", buttons)
        self.assertNotIn("inquiries_quoterequest_close_submit", buttons)  # pas encore acceptée
        self.client.post(self.url("change"), change_form_data(
            response, inquiries_quoterequest_refuse_submit=""))
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, QStatus.REFUSEE)

    def test_bulk_assign_to_me(self):
        commercial = self.login("COMMERCIAL")
        other = make_quote(status=QStatus.TERMINEE)
        self.client.post(reverse("admin:inquiries_quoterequest_changelist"), {
            "action": "assign_to_me", "_selected_action": [self.quote.pk, other.pk],
        })
        self.quote.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(self.quote.assigned_to, commercial)
        self.assertIsNone(other.assigned_to)  # devis clos : ignoré

    def test_quotes_cannot_be_created_from_the_backoffice(self):
        self.login("ADMIN")
        self.assertEqual(self.client.get(reverse("admin:inquiries_quoterequest_add")).status_code, 403)

    def test_manager_role_has_no_access_to_quotes(self):
        self.login("GESTIONNAIRE")
        self.assertEqual(self.client.get(self.url("change")).status_code, 403)


class ContactMessageAdminTests(AdminTestCase):
    def setUp(self):
        self.message = ContactMessage.objects.create(
            name="Koffi", email="koffi@example.com", subject="Visa Canada", message="Bonjour…")

    def url(self, name):
        return reverse(f"admin:inquiries_contactmessage_{name}", args=[self.message.pk])

    def test_opening_a_new_message_marks_it_read(self):
        self.login("COMMERCIAL")
        response = self.client.get(self.url("change"))
        self.assertContains(response, "mailto:koffi@example.com")
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, ContactMessage.Status.LU)

    def test_read_only_roles_do_not_change_the_status(self):
        self.login("AGENT")  # aucun droit sur les messages
        self.assertEqual(self.client.get(self.url("change")).status_code, 403)
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, ContactMessage.Status.NOUVEAU)

    def test_archive_button(self):
        self.login("COMMERCIAL")
        response = self.client.get(self.url("change"))
        self.client.post(self.url("change"), change_form_data(
            response, inquiries_contactmessage_archive_submit=""))
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, ContactMessage.Status.ARCHIVE)
