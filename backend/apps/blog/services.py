from django.utils import timezone

from apps.core.exceptions import InvalidTransition

from .models import BlogPost


def publish_post(post, at=None):
    """Publie un article, immédiatement ou à une date programmée."""
    if post.status == BlogPost.Status.PUBLIE and at is None:
        raise InvalidTransition("Cet article est déjà publié.")
    post.status = BlogPost.Status.PUBLIE
    post.published_at = at or post.published_at or timezone.now()
    post.save()
    return post


def unpublish_post(post):
    post.status = BlogPost.Status.BROUILLON
    post.save()
    return post
