from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.blog import services
from apps.blog.models import BlogPost
from apps.core.exceptions import InvalidTransition
from apps.core.tests.admin_helpers import AdminTestCase, change_form_data
from apps.core.tests.factories import BlogPostFactory

Status = BlogPost.Status


class PublicationTests(AdminTestCase):
    def test_publish_now_then_back_to_draft(self):
        post = services.publish_post(BlogPostFactory())
        self.assertEqual(post.status, Status.PUBLIE)
        self.assertLessEqual(post.published_at, timezone.now())
        self.assertIn(post, BlogPost.objects.published())
        with self.assertRaises(InvalidTransition):
            services.publish_post(post)

        post = services.unpublish_post(post)
        self.assertEqual(post.status, Status.BROUILLON)
        self.assertNotIn(post, BlogPost.objects.published())

    def test_scheduled_publication_stays_hidden_until_its_date(self):
        tomorrow = timezone.now() + timedelta(days=1)
        post = services.publish_post(BlogPostFactory(), at=tomorrow)
        self.assertEqual(post.published_at, tomorrow)
        self.assertNotIn(post, BlogPost.objects.published())

    def test_reading_time_is_computed_on_save(self):
        post = BlogPostFactory(content="mot " * 450)
        self.assertEqual(post.reading_time, 3)  # 450 mots à 200 mots par minute

    def test_admin_bulk_actions_use_the_services(self):
        self.login("AGENT")
        draft, published = BlogPostFactory(), services.publish_post(BlogPostFactory())
        url = reverse("admin:blog_blogpost_changelist")
        response = self.client.post(url, {"action": "publish_now",
                                          "_selected_action": [draft.pk, published.pk]}, follow=True)
        self.assertContains(response, "1 article(s) publié(s).")  # l'autre l'était déjà
        draft.refresh_from_db()
        self.assertEqual(draft.status, Status.PUBLIE)
        self.assertIsNotNone(draft.published_at)

        self.client.post(url, {"action": "back_to_draft", "_selected_action": [draft.pk, published.pk]})
        self.assertFalse(BlogPost.objects.filter(status=Status.PUBLIE).exists())

    def test_publishing_from_the_form_dates_the_article(self):
        self.login("AGENT")
        post = BlogPostFactory()
        url = reverse("admin:blog_blogpost_change", args=[post.pk])
        self.client.post(url, change_form_data(self.client.get(url), status=Status.PUBLIE, _save=""))
        post.refresh_from_db()
        self.assertEqual(post.status, Status.PUBLIE)
        self.assertIsNotNone(post.published_at)
