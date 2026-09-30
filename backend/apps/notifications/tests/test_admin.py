from django.urls import reverse

from apps.core.tests.admin_helpers import AdminTestCase
from apps.core.tests.factories import NotificationFactory, UserFactory
from apps.notifications.models import Notification


def notify(user, **kwargs):
    return NotificationFactory(recipient=user, **kwargs)


class NotificationAdminTests(AdminTestCase):
    def test_each_member_only_sees_their_notifications(self):
        agent = self.login("AGENT")  # aucun droit particulier : ses notifications seulement
        mine = notify(agent, title="Pour moi")
        notify(UserFactory(role="COMMERCIAL"), title="Pour un collègue")
        response = self.client.get(reverse("admin:notifications_notification_changelist"))
        self.assertContains(response, "Pour moi")
        self.assertNotContains(response, "Pour un collègue")
        others = Notification.objects.exclude(pk=mine.pk).get()
        url = reverse("admin:notifications_notification_change", args=[others.pk])
        self.assertNotEqual(self.client.get(url).status_code, 200)

    def test_opening_marks_as_read_and_follows_the_link(self):
        user = self.login("COMMERCIAL")
        notification = notify(user)
        response = self.client.get(
            reverse("admin:notifications_notification_open_detail", args=[notification.pk]))
        self.assertRedirects(response, notification.link, fetch_redirect_response=False)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_external_links_are_not_followed(self):
        user = self.login("COMMERCIAL")
        notification = notify(user, link="https://evil.example.com/")
        response = self.client.get(
            reverse("admin:notifications_notification_open_detail", args=[notification.pk]))
        self.assertRedirects(
            response, reverse("admin:notifications_notification_change", args=[notification.pk]))

    def test_mark_all_read_asks_for_confirmation(self):
        user = self.login("GESTIONNAIRE")
        notify(user)
        notify(user)
        url = reverse("admin:notifications_notification_mark_all_read")
        self.client.get(url)
        self.assertEqual(Notification.objects.filter(is_read=False).count(), 2)
        self.client.post(url)
        self.assertFalse(Notification.objects.filter(is_read=False).exists())
