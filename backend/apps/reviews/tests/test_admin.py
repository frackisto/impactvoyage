from django.urls import reverse

from apps.core.tests.admin_helpers import AdminTestCase
from apps.reviews.models import Review


def make_review(**kwargs):
    defaults = {"author_name": "Mariam", "author_email": "mariam@example.com", "rating": 5,
                "comment": "Parfait"}
    return Review.objects.create(**{**defaults, **kwargs})


class ReviewAdminTests(AdminTestCase):
    def moderate(self, action, *reviews):
        return self.client.post(reverse("admin:reviews_review_changelist"), {
            "action": action, "_selected_action": [r.pk for r in reviews],
        }, follow=True)

    def test_manager_approves_and_features_reviews(self):
        self.login("GESTIONNAIRE")
        first, second = make_review(), make_review(author_name="Serge")
        self.moderate("approve", first)
        self.moderate("approve_and_feature", first, second)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.status, first.is_featured), (Review.Status.APPROUVE, True))
        self.assertEqual((second.status, second.is_featured), (Review.Status.APPROUVE, True))

    def test_reject_reports_reviews_already_refused(self):
        self.login("GESTIONNAIRE")
        review = make_review(status=Review.Status.REFUSE)
        response = self.moderate("reject", review)
        self.assertContains(response, "Cet avis a déjà ce statut.")

    def test_commercial_can_only_read_reviews(self):
        self.login("COMMERCIAL")
        review = make_review()
        self.assertEqual(self.client.get(reverse("admin:reviews_review_changelist")).status_code, 200)
        self.moderate("approve", review)
        review.refresh_from_db()
        self.assertEqual(review.status, Review.Status.EN_ATTENTE)
