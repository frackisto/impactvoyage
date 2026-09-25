from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.exceptions import InvalidTransition
from apps.core.tests.helpers import make_tour, make_user
from apps.notifications.models import Notification
from apps.reviews import selectors, services
from apps.reviews.models import Review


class ReviewTests(TestCase):
    def test_submit_moderate_and_summarize(self):
        manager = make_user("GESTIONNAIRE")
        tour = make_tour()
        review = services.submit_review(
            author_name="Fatou", author_email="fatou@example.com", rating=5,
            comment="Superbe circuit !", tour=tour,
        )
        self.assertEqual(review.status, Review.Status.EN_ATTENTE)
        self.assertTrue(Notification.objects.filter(recipient=manager).exists())
        self.assertEqual(selectors.rating_summary(tour=tour)["count"], 0)

        services.approve_review(review, featured=True)
        self.assertEqual(selectors.rating_summary(tour=tour), {"average": 5.0, "count": 1})
        with self.assertRaises(InvalidTransition):
            services.approve_review(review)

    def test_invalid_rating_is_rejected_before_saving(self):
        with self.assertRaises(ValidationError):
            services.submit_review(
                author_name="X", author_email="x@example.com", rating=0, comment="…"
            )
