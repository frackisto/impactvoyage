from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import translation

from apps.blog.models import BlogPost
from apps.core.files import UploadTo
from apps.core.models import SiteSettings
from apps.core.tests.factories import DestinationFactory, TourFactory
from apps.events.models import Event, EventImage
from apps.reviews.models import Review


class UploadToTests(TestCase):
    def test_renames_file_to_uuid_in_model_folder(self):
        path = UploadTo()(DestinationFactory(), "Photo Plage.JPG")
        folder, name = path.split("/")
        self.assertEqual(folder, "destinations")
        self.assertRegex(name, r"^[0-9a-f]{32}\.jpg$")


class SiteSettingsTests(TestCase):
    def test_is_a_singleton(self):
        SiteSettings.objects.create(agency_name="A")
        SiteSettings(agency_name="B").save()
        self.assertEqual(SiteSettings.objects.count(), 1)
        self.assertEqual(SiteSettings.load().agency_name, "B")


class TranslationTests(TestCase):
    def test_english_falls_back_to_french_when_empty(self):
        destination = DestinationFactory(name_fr="Côte d'Ivoire", name_en="")
        with translation.override("en"):
            self.assertEqual(destination.name, "Côte d'Ivoire")
        destination.name_en = "Ivory Coast"
        with translation.override("en"):
            self.assertEqual(destination.name, "Ivory Coast")


class ContentConstraintTests(TestCase):
    def test_review_rating_must_be_between_1_and_5(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Review.objects.create(author_name="X", author_email="x@x.com", rating=6, comment="…")

    def test_review_targets_at_most_one_page(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Review.objects.create(
                author_name="X", author_email="x@x.com", rating=5, comment="…",
                destination=DestinationFactory(), tour=TourFactory(),
            )

    def test_published_blog_post_requires_a_date(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            BlogPost.objects.create(
                title="T", slug="t", excerpt="E", content="C", status=BlogPost.Status.PUBLIE
            )

    def test_blog_reading_time_is_computed(self):
        post = BlogPost.objects.create(title="T", slug="t", excerpt="E", content="mot " * 450)
        self.assertEqual(post.reading_time, 3)

    def test_video_media_requires_a_url(self):
        event = Event.objects.create(
            title="Salon", slug="salon", description="…", category=Event.Category.PROFESSIONNEL,
            date="2026-10-01", location="Abidjan",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            EventImage.objects.create(event=event, type=EventImage.Type.VIDEO)
        EventImage.objects.create(
            event=event, type=EventImage.Type.VIDEO, video_url="https://youtu.be/x"
        )
