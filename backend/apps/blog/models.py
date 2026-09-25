import math
import re

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import Category, CoverImageMixin, SlugMixin, Tag, TimeStampedModel

WORDS_PER_MINUTE = 200


class BlogPostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=BlogPost.Status.PUBLIE, published_at__lte=timezone.now())


class BlogPost(TimeStampedModel, SlugMixin, CoverImageMixin):
    """Article de conseils voyage — CdC § 21."""

    UPLOAD_FOLDER = "blog"

    class Status(models.TextChoices):
        BROUILLON = "BROUILLON", "Brouillon"
        PUBLIE = "PUBLIE", "Publié"

    title = models.CharField("titre", max_length=200)
    excerpt = models.CharField("résumé", max_length=400)
    content = models.TextField("contenu")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
        verbose_name="auteur",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
        limit_choices_to={"kind": Category.Kind.BLOG},
        verbose_name="catégorie",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="blog_posts")
    seo_title = models.CharField("titre SEO", max_length=70, blank=True)
    seo_description = models.CharField("description SEO", max_length=160, blank=True)
    status = models.CharField(
        "statut", max_length=10, choices=Status.choices, default=Status.BROUILLON, db_index=True
    )
    published_at = models.DateTimeField("publié le", null=True, blank=True, db_index=True)
    reading_time = models.PositiveSmallIntegerField(
        "temps de lecture (min)", default=1, editable=False
    )

    objects = BlogPostQuerySet.as_manager()

    class Meta:
        verbose_name = "article"
        ordering = ["-published_at", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(status="PUBLIE") | Q(published_at__isnull=False),
                name="blogpost_published_has_date",
            ),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", self.content or "")))
        self.reading_time = max(1, math.ceil(words / WORDS_PER_MINUTE))
        super().save(*args, **kwargs)
